# Contributing Guidelines

Contributions are welcome from the community. Questions can be asked on the
[issues page][1]. Before creating a new issue, please take a moment to search
and make sure a similar issue does not already exist. If one does exist, you
can comment (most simply even with just a `+1`) to show your support for that
issue.

If you have direct contributions you would like considered for incorporation
into the project you can [fork this repository][2] and
[submit a merge request][3] for review.

For additional information, please see the [USGS software development best
practices guide][4] and the [USGS Code of Scientific Conduct][5]. 

The big picture guidelines are: 

- Submit changes via a pull request from a feature branch section on Merge Requests for more details.
- We generally try to follow [pep8](https://www.python.org/dev/peps/pep-0008/) as much as possible.
- Include doc strings for all public methods. We use the [Google][6] doc string style.
- Please use [black][7] to format python code.
- Use Python's [built-in][8] exceptions as much as possible.


## Merge Request Guidelines

1. Use concise, yet informative commit messages.
2. Rebase (if you know how) to provide an easy-to-follow history of changes in your branch.
3. Update the changelog (`CHANGELOG.md`) for significant changes into the "main" section.
4. Update docs if relevant.
5. Add unit tests for any new features.
6. Run the unit tests (we use ``pytest``) prior to sending in your changes.

### Commit Messages

Commit messages should begin with a one line concise yet informative summary.
A blank line should separate the one line summary from any additional information.
We strongly recommend using the following templates, in which the first starts with
a commit type (in all caps) that indicates the type of changes in the commit.

For example, a commit related to documentation would look like:

```
DOCS: [one line description]

[Optional additional information]
```

We use the set of commit types from the [angular][9] project:
* **BUILD**: Changes that affect the build system or external dependencies (e.g., pyproject.toml)
* **CI**: Changes to our CI configuration files and scripts (e.g., .gitlab-ci.yml)
* **DOCS**: Documentation only changes
* **FEAT**: A new feature
* **FIX**: A bug fix
* **PERF**: A code change that improves performance
* **REFACTOR**: A code change that neither fixes a bug nor adds a feature
* **STYLE**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
* **TEST**: Adding missing tests or correcting existing tests


### Rebasing

:::{danger}
Rebasing can do permanent damage to your branch if you do not do it correctly.
Practice on a scratch repository until you are comfortable with how rebasing works.
:::

You can use rebasing to clean up the history of commits in a branch to make the changes easier to follow.
Common reasons to rebase include:

* squashing (combining) several closely related commits into a single commit,
* reordering commits, especially to allow squashing, and
* dropping (removing) commits related to debugging.


## Releases

1. Create a release candidate branch with a name related to the release version like `v1.2.1.rc0`.
2. Update `code.json`, this is now automated with the `esi-releases` package. For example, use the following command to increase the minor version number (options are "major", "minor", and "patch"):
   ```
   releases minor
   ```
3. Update `CHANGELOG.md` to include the changes for this version. The goal is for the changelog to be kept up to date with each merge request, so this step should largely consist of creating a new section for this release and moving content into it from "main". 
4. Commit changes to the `v1.2.1.rc0` branch.
5. Push the branch to your origin.
   ```
   git push origin v1.2.1.rc0
   ```
6. Create a merge request in to upstream main, merge it, and rebase locally.
7. Create an annotated tag **from main** and push the tag upstream
   ```
   git tag -a v1.2.1 -m "Version 1.2.1"
   git push upstream v1.2.1
   ```
   - This git push command is what triggers the "release" pipeline that includes the test, build, and deploy stages.
   - *Note that we cannot have a hyphen in the tag name.* 
   - Also, if we end the tag name with "dev" then it will be build and uploaded to pypi as a pre-release version, which means that it will never be pip installed unless the user specifies the exact version of the pre-release.
   - Maintenance note: the PYPI tokens are maintained in gitlab for the ESI group, under Settings then CI/CD, then Variables. These tokens are associated with the "pager_cicd" pypi service account.  
8. Create release from tag in gitlab. Give it a release title like `v1.2.1`.
9. Copy/paste the relevant part of the changelog into the "describe this release" section.


## Build Documentation

Some additional packages are required to build the documentation, which can be included
with the `doc` install option, e.g.,

```
pip install .[doc]
```

Then the docs are built with

```
cd docs/
./makedocs.sh
```

Note that the script includes the follow arguments:
 - `rebuild` - Build documentation from a clean starting point.
 - `update` - Incremental build of the documentation. No cleaning.
 - `clean_data` - Remove all temporary data files generated when building the documentation.
 - `clean_all` - Remove all temporary data files and generated documentation.


Notes:
 - Never commit the built documentation files.
 - Remember that the notebooks run gmprocess code when you build the docs, 
   so please be sure to check that the tutorials ran successfully. 
 - The result of the tutorials will depend on your config file options, 
   so I recommend having a project with the default config file set up 
   and use that project when building the docs. 


[1]: https://code.usgs.gov/ghsc/esi/groundmotion-processing/issues
[2]: https://docs.gitlab.com/ee/user/project/repository/forking_workflow.html
[3]: https://docs.gitlab.com/ee/user/project/merge_requests/
[4]: https://www.usgs.gov/products/software/software-management
[5]: https://www.usgs.gov/about/organization/science-support/science-quality-and-integrity/fundamental-science-practices
[6]: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
[7]: https://github.com/psf/black
[8]: https://docs.python.org/3.8/library/exceptions.html#built-in-exceptions
[9]: https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#type