# Bug Reports

(bug_reports)=

## Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to investigate carefully, collect information and describe the issue in detail in your report. Please complete the following steps in advance to help us fix any potential bug as fast as possible.

* Make sure that you are using the latest version.
* Determine if your bug is really a bug and not an error on your side e.g. using incompatible environment components/versions (Make sure that you have read the documentation. If you are looking for support, you might want to check this section).
* To see if other users have experienced (and potentially already solved) the same issue you are having, check if there is not already a bug report existing for your bug or error in the bug tracker.
* Also make sure to search the internet (including Stack Overflow) to see if users outside of the GitHub community have discussed the issue.
* Collect information about the bug:
  * Stack trace (Traceback)
  * OS, Platform and Version (Windows, Linux, macOS, x86, ARM)
  * Version of the interpreter, compiler, SDK, runtime environment, package manager, depending on what seems relevant.
  * Possibly your input and the output
  * Can you reliably reproduce the issue? And can you also reproduce it with older versions?

## How Do I Submit a Good Bug Report?

You must never report security related issues, vulnerabilities or bugs including sensitive information to the issue tracker, or elsewhere in public. Instead sensitive bugs must be sent by email to .
We use GitHub issues to track bugs and errors. If you run into an issue with the project:

* Open an Issue. (Since we can't be sure at this point whether it is a bug or not, we ask you not to talk about a bug yet and not to label the issue.)
* Explain the behavior you would expect and the actual behavior.
* Please provide as much context as possible and describe the reproduction steps that someone else can follow to recreate the issue on their own. This usually includes your code. For good bug reports you should isolate the problem and create a reduced test case.
* Provide the information you collected in the previous section.

Once it's filed:
* The project team will label the issue accordingly.
* A team member will try to reproduce the issue with your provided steps. If there are no reproduction steps or no obvious way to reproduce the issue, the team will ask you for those steps and mark the issue as needs-repro. Bugs with the needs-repro tag will not be addressed until they are reproduced.
* If the team is able to reproduce the issue, it will be marked needs-fix, as well as possibly other tags (such as critical), and the issue will be left to be implemented by someone.
