"""aiida_aimall.workchains
Workchains designed for a workflow starting from a set of cmls, then breaking off into fragment Gaussian Calculations
Needs to be run in part with aiida_aimall.controllers to control local traffic on lab Mac
Example in the works

Provided Workchains are
MultiFragmentWorkchain, entry point: multifrag
G16OptWorkChain, entry point: g16opt
AimAllReor WorkChain, entry point: aimreor
"""
import sys

import pandas as pd
from aiida.engine import ToContext, WorkChain, calcfunction
from aiida.orm import Code, Dict, SinglefileData, Str, load_group
from aiida.orm.extras import EntityExtras
from aiida.plugins.factories import CalculationFactory, DataFactory
from group_decomposition.fragfunctions import (
    count_uniques,
    identify_connected_fragments,
    merge_uniques,
    output_ifc_dict,
)
from group_decomposition.utils import all_data_from_cml, list_to_str, xyz_list_to_str
from subproptools.sub_reor import rotate_substituent_aiida

old_stdout = sys.stdout

# load the needed calculations and data types
GaussianCalculation = CalculationFactory("gaussianwfx")
AimqbParameters = DataFactory("aimall")
AimqbCalculation = CalculationFactory("aimall")
DictData = DataFactory("dict")
PDData = DataFactory("dataframe.frame")


@calcfunction
def generate_rotated_structure_aiida(FolderData, atom_dict, cc_dict):
    """Rotates the fragment to the defined coordinate system

    Args:
        FolderData: aim calculation folder
        atom_dict: AIM atom dict
        cc_dict: AIM cc_dict
    """
    return Dict(rotate_substituent_aiida(FolderData, atom_dict, cc_dict))


@calcfunction
def dict_to_structure(fragment_dict):
    """Generate a string of xyz coordinates for Gaussian input file

    :param fragment_dict:
    :param type fragment_dict: aiida.orm.nodes.data.dict.Dict
    """
    inp_dict = fragment_dict.get_dict()
    symbols = inp_dict["atom_symbols"]
    coords = inp_dict["geom"]
    outstr = ""
    for i, symbol in enumerate(symbols):
        if i != len(symbols) - 1:
            outstr = (
                outstr
                + symbol
                + "   "
                + str(coords[i][0])
                + "   "
                + str(coords[i][1])
                + "   "
                + str(coords[i][2])
                + "\n"
            )
        else:
            outstr = (
                outstr
                + symbol
                + "   "
                + str(coords[i][0])
                + "   "
                + str(coords[i][1])
                + "   "
                + str(coords[i][2])
            )
    return Str(outstr)


@calcfunction
def parse_cml_files(singlefiledata):
    """Extract needed data from cml

    Args:
        singlefiledata: cml file stored in database as SinglefileData"""
    return Dict(all_data_from_cml(singlefiledata.get_content().split("\n")))


@calcfunction
def generate_cml_fragments(params, cml_Dict):
    """Fragment the molecule defined by a CML

    Args:
        params: parameters for the fragmenting
        cml_Dict: results of parse_cml_files
    Returns:
        dict
    """
    # pylint:disable=too-many-locals
    cml_list = (
        cml_Dict.get_dict().values()
    )  # maybe just don't store cml files in database, just pass list to cgis here
    param_dict = params.get_dict()  # get dict from aiida node
    input_type = param_dict["input_type"]  # should set to cmldict
    bb_patt = param_dict["bb_patt"]
    frame_list = []
    done_smi = []
    dict_list = []
    out_frame = pd.DataFrame()
    for inp in cml_list:
        print(inp)
        frame = identify_connected_fragments(
            inp, bb_patt=bb_patt, input_type=input_type, include_parent=True
        )
        frame_list.append(frame)
        mol = frame.at[0, "Parent"]
        frag_dict, done_smi = output_ifc_dict(mol, frame, done_smi)
        dict_list.append(frag_dict)
        if frame is not None:
            unique_frame = count_uniques(frame, False, uni_smi_type=True)
            if out_frame.empty:
                out_frame = unique_frame
            else:
                out_frame = merge_uniques(out_frame, unique_frame, True)
    out_frame = out_frame.drop("Molecule", axis=1)
    out_frame = out_frame.drop("Parent", axis=1)

    out_dict = {}
    for key, value in frag_dict.items():
        rep_key = (
            key.replace("*", "Att")
            .replace("#", "t")
            .replace("(", "_")
            .replace(")", "_")
            .replace("-", "Neg")
            .replace("+", "Pos")
            .replace("[", "")
            .replace("]", "")
            .replace("=", "d")
        )
        out_dict[rep_key] = DictData(value)
    col_names = list(out_frame.columns)
    # Find indices of relevant columns
    xyz_idx = col_names.index("xyz")
    atom_idx = col_names.index("Atoms")
    label_idx = col_names.index("Labels")
    type_idx = col_names.index("atom_types")
    count_idx = col_names.index("count")
    nat_idx = col_names.index("numAttachments")
    out_frame["xyzstr"] = out_frame.apply(
        lambda row: xyz_list_to_str(row[xyz_idx]), axis=1
    )
    out_frame["atomstr"] = out_frame.apply(
        lambda row: list_to_str(row[atom_idx]), axis=1
    )
    out_frame["labelstr"] = out_frame.apply(
        lambda row: list_to_str(row[label_idx]), axis=1
    )
    out_frame["typestr"] = out_frame.apply(
        lambda row: xyz_list_to_str(row[type_idx]), axis=1
    )
    out_frame["countstr"] = out_frame.apply(lambda row: str(row[count_idx]), axis=1)
    out_frame["numatstr"] = out_frame.apply(lambda row: str(row[nat_idx]), axis=1)
    out_frame = out_frame.drop("xyz", axis=1)
    out_frame = out_frame.drop("Atoms", axis=1)
    out_frame = out_frame.drop("Labels", axis=1)
    out_frame = out_frame.drop("atom_types", axis=1)
    out_frame = out_frame.drop("count", axis=1)
    out_frame = out_frame.drop("numAttachments", axis=1)
    out_dict["cgis_frame"] = PDData(out_frame)
    return out_dict


# @calcfunction
# def dict_to_structure(fragment_dict):
#     """Generate a string of xyz coordinates for Gaussian input file

#     :param fragment_dict:
#     :param type fragment_dict: aiida.orm.nodes.data.dict.Dict
#     """
#     inp_dict = fragment_dict.get_dict()
#     symbols = inp_dict["atom_symbols"]
#     coords = inp_dict["geom"]
#     outstr = ""
#     for i in range(0, len(symbols)):
#         if i != len(symbols) - 1:
#             outstr = (
#                 outstr
#                 + symbols[i]
#                 + "   "
#                 + str(coords[i][0])
#                 + "   "
#                 + str(coords[i][1])
#                 + "   "
#                 + str(coords[i][2])
#                 + "\n"
#             )
#         else:
#             outstr = (
#                 outstr
#                 + symbols[i]
#                 + "   "
#                 + str(coords[i][0])
#                 + "   "
#                 + str(coords[i][1])
#                 + "   "
#                 + str(coords[i][2])
#             )
#     return Str(outstr)


@calcfunction
def update_g16_params(g16dict, fragdict):
    """Update input g16 params with charge and multiplicity

    :param g16dict:
    :param type g16dict: aiida.orm.nodes.data.dict.Dict
    """
    param_dict = g16dict.get_dict()
    frag_dict = fragdict.get_dict()
    param_dict.update({"charge": frag_dict["charge"]})
    param_dict.update({"multiplicity": 1})
    return Dict(dict=param_dict)


class MultiFragmentWorkChain(WorkChain):
    """Workchain to fragment a cml file and generate gaussian calculations on each fragment"""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input("cml_file_dict", valid_type=Dict)
        spec.input("frag_params", valid_type=Dict)
        spec.input("g16_code", valid_type=Code)
        # spec.input('aim_code',valid_type=Code)
        # spec.input('aim_params',valid_type=AimqbParameters)
        spec.input("g16_opt_params", valid_type=Dict)
        # spec.input('g16_sp_params',valid_type=Dict)
        spec.outline(cls.generate_fragments, cls.submit_fragmenting)

    def generate_fragments(self):
        """perform the fragmenting"""
        self.ctx.fragments = generate_cml_fragments(
            self.inputs.frag_params, self.inputs.cml_file_dict
        )

    def submit_fragmenting(self):
        """submit all the fragmenting jobs as gaussian calculations"""
        for key, molecule in self.ctx.fragments.items():
            # print(molecule)
            if isinstance(molecule, Dict):
                self.submit(
                    G16OptWorkchain,
                    g16_opt_params=self.inputs.g16_opt_params,
                    fragment_dict=molecule,
                    frag_label=Str(key),
                    g16_code=self.inputs.g16_code,
                )
                # aim_code=self.inputs.aim_code,
                # aim_params=self.inputs.aim_params,
                # g16_sp_params = self.inputs.g16_sp_params)


class G16OptWorkchain(WorkChain):
    """Run G16 Calculation on a fragment produced by MultiFragmentWorkChain

    Process continues through the use of AimReorSubmissionController
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input("g16_opt_params", valid_type=Dict)
        spec.input("fragment_dict", valid_type=Dict)
        spec.input("frag_label", valid_type=Str)
        spec.input("g16_code", valid_type=Code)
        spec.input("wfxgroup", valid_type=Str, default=Str("opt_wfx"))
        spec.outline(
            cls.dict_to_struct,
            cls.update_g16_param,
            cls.g16_opt,
        )  # ,cls.aimall)#, cls.aimall,cls.reorient,cls.aimall)

    def dict_to_struct(self):
        """Generate the structure input in Gaussian Format"""
        self.ctx.structure = dict_to_structure(self.inputs.fragment_dict)

    def update_g16_param(self):
        """Update parameters with correct charge and multiplicity"""
        self.ctx.params_with_cm = update_g16_params(
            self.inputs.g16_opt_params, self.inputs.fragment_dict
        )

    def g16_opt(self):
        """Submit the Gaussian optimization"""
        builder = GaussianCalculation.get_builder()
        builder.structure_str = self.ctx.structure
        builder.parameters = self.ctx.params_with_cm
        builder.fragment_label = self.inputs.frag_label
        builder.code = self.inputs.g16_code
        builder.wfxgroup = self.inputs.wfxgroup
        builder.metadata.options.resources = {"num_machines": 1, "tot_num_mpiprocs": 1}
        builder.metadata.options.max_memory_kb = 384000
        builder.metadata.options.max_wallclock_seconds = 604800
        process_node = self.submit(builder)
        g16_opt_group = load_group("g16_opt")
        g16_opt_group.add_nodes(process_node)
        out_dict = {"opt": process_node}
        # self.ctx.standard_wfx = process_node.get_outgoing().get_node_by_label("wfx")
        return ToContext(out_dict)


class AIMAllReor(WorkChain):
    """Workchain to run AIM and then reorient the molecule using the results

    Process continues in GaussianSubmissionController"""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input("aim_params", valid_type=AimqbParameters)
        spec.input("file", valid_type=SinglefileData)
        # spec.output('aim_dict',valid_type=Dict)
        spec.input("aim_code", valid_type=Code)
        spec.input("frag_label", valid_type=Str)
        spec.outline(
            cls.aimall, cls.rotate, cls.dict_to_struct_reor
        )  # ,cls.aimall)#, cls.aimall,cls.reorient,cls.aimall)

    def aimall(self):
        """submit the aimall calculation"""
        builder = AimqbCalculation.get_builder()
        builder.code = self.inputs.aim_code
        builder.parameters = self.inputs.aim_params
        builder.file = self.inputs.file
        builder.metadata.options.resources = {
            "num_machines": 1,
            "tot_num_mpiprocs": 2,
        }
        aim_calc = self.submit(builder)
        aim_noreor_group = load_group("prereor_aim")
        aim_noreor_group.add_nodes(aim_calc)
        out_dict = {"aim": aim_calc}
        return ToContext(out_dict)

    def rotate(self):
        """perform the rotation"""
        aimfolder = self.ctx["aim"].get_outgoing().get_node_by_label("retrieved")
        output_dict = (
            self.ctx["aim"]
            .get_outgoing()
            .get_node_by_label("output_parameters")
            .get_dict()
        )
        atom_props = output_dict["atomic_properties"]
        cc_props = output_dict["cc_properties"]
        self.ctx.rot_struct_dict = generate_rotated_structure_aiida(
            aimfolder, atom_props, cc_props
        )

    def dict_to_struct_reor(self):
        """generate the gaussian input from rotated structure"""
        struct_dict = dict_to_structure(self.ctx.rot_struct_dict)
        reor_struct_group = load_group("reor_structs")
        reor_struct_group.add_node(struct_dict)
        struct_extras = EntityExtras(struct_dict)
        struct_extras.set("smiles", self.frag_label.value)
        self.ctx.rot_structure = struct_dict