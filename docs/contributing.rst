Contributing
============

Open source software thrives on people's contributions.
We sincerely appreciate your interest in contributing to the MorphoCluster project!

Bug Reports
-----------

Bug reports play a vital role!
Before submitting a bug report, please take a moment to check
the `GitHub issues`_ to ensure that the bug hasn't already
been reported.

.. _GitHub issues: https://github.com/morphocut/morphocluster/issues

Code Contributions
------------------

Steps for Submitting Code
~~~~~~~~~~~~~~~~~~~~~~~~~

GitHub Pull Requests are the preferred method for collaborating
on code in this project.
To contribute, please follow these steps:

1. Fork the MorphoCluster `repository`_ on GitHub and clone your fork locally:

   ..  code-block:: sh

      git clone ...

   (Insert the URL of your fork.)

2. Configure the the "upstream" remote to be able to get the latest changes from the central repository:

   ..  code-block:: sh

      git remote add upstream https://github.com/morphocluster/morphocluster.git

   (This only needs to be done once for each local clone.)

2. Create a new branch for the fix or feature that you're about to implement:

   ..  code-block:: sh

      # Switch to "main" branch
      git checkout main

      # Pull the latest changes from the central repository
      git pull upstream main

      # Push the latest changes to your fork (optional)
      git push

      # Create and checkout a new branch named "fix-xy"
      git checkout -b fix-xy

   (`fix-xy` is a placeholder. Chose a speaking name.)

3. Implement your changes.

4. Write `meaningful commit messages <https://chris.beams.io/posts/git-commit/>`_ to document your changes.

5. Push your local changes to your fork on GitHub:

   ..  code-block:: sh
      
      git push -u origin fix-xy

6. Submit a GitHub Pull Request. Your contribution will be reviewed promptly.

.. _repository: https://github.com/morphocut/morphocut

7. It might happen that new changes appear on the upstream main branch.
   These need to be merged into your feature branch:

   ..  code-block:: sh

      # Pull the latest changes from the central repository
      git pull upstream main
   


VS Code Dev Container
~~~~~~~~~~~~~~~~~~~~~
The repository contains a VS Code `.devcontainer` configuration.
See the official VS Code documentation: `Developing inside a Container <https://code.visualstudio.com/docs/devcontainers/containers>`_.

To build the devcontainer Docker image, `BuildKit <https://docs.docker.com/build/buildkit/>`_ is required.
It is recommended to include the following in your `.bashrc`:

..  code-block:: sh

   # Use BuildKit
   DOCKER_BUILDKIT=1
   COMPOSE_DOCKER_CLI_BUILD=1
   BUILDKIT_PROGRESS=plain

Running the services
''''''''''''''''''''

Both the backend (Flask) and frontend (Vue) frameworks support hot reloading.
This means that after saving the code from the editor, the services reload automatically
and changes should be visible instantaneously.
To enable this behavior, open two terminals, one for the backend, one for the frontend.

Backend:

..  code-block:: sh

   cd morphocluster/frontend
   flask run

   # The output looks similar to this:

      * Serving Flask app "morphocluster" (lazy loading)
      * Environment: development
      * Debug mode: on
      * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
      * Restarting with stat
      * Debugger is active!
      * Debugger PIN: XXX-XXX-XXX


Frontend:

..  code-block:: sh
   
   cd morphocluster/frontend
   npm run serve

   # The frontend is built in-place.
   # After a while, the output looks similar to this:

      DONE  Compiled successfully in 5040ms

      App running at:
      - Local:   http://localhost:8080/frontend/ 
      - Network: http://172.25.0.2:8080/frontend/

      Note that the development build is not optimized.
      To create a production build, run npm run build.


Then, open the address of the frontend in your browser.



Updating dependencies
~~~~~~~~~~~~~~~~~~~~~

Dependencies are declared in `environment.base.yaml` (general) and `environment.dev.yaml` (development only).
Run `gen_conda-lock.sh` to regenerate the lock file, then rebuild the devcontainer.


Code Style
~~~~~~~~~~

To maintain code consistency,
please adhere to the following guidelines:

* Follow `PEP 8`_, `PEP 257`_, and the `Google Style Guide`_.
* Utilize `black <https://black.readthedocs.io/en/stable/>`_ to format your code.
* Use `isort <https://pypi.org/project/isort/>`_ to organize your imports.
* Employ `pydocstyle <https://pypi.org/project/pydocstyle/>`_ to receive feedback on your docstrings.

.. _Google Style Guide: http://google.github.io/styleguide/pyguide.html
.. _PEP 8: https://www.python.org/dev/peps/pep-0008/
.. _PEP 257: https://www.python.org/dev/peps/pep-0257/


Documentation Contributions
---------------------------

Documentation holds significant value for this library,
and we warmly welcome any improvements.
The documentation resides in the ``docs/`` directory and is written in `reStructuredText`_.
We utilize `Sphinx`_ to generate a comprehensive suite of documentation,
with `napoleon`_ interpreting the docstrings.

To build and preview the documentation, perform the following steps:

..  code-block:: sh

   cd docs

   # Render docs as html
   make html

   # Start local webserver to display the docs
   python -m http.server -d _build/html/


.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _Sphinx: http://sphinx-doc.org/index.html
.. _napoleon: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/
