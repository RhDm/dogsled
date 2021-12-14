Quick tour
=====================================

The simplest dogsled installation can be done via `Conda <https://docs.conda.io/en/latest//>`__ using :code:`environment.yml` file for Linux and macOS and :code:`win_environment.yml` for Windows

.. hint::

    It is highly recommended not to install dogsled (or any other package) in the base environment, create a new one using `Conda <https://docs.conda.io/en/latest/>`__ or `venv <https://docs.python.org/3/library/venv.html/>`__

.. code-block:: console

    user@arch:~$ git clone https://github.com/RhDm/dogsled.git
    user@arch:~$ cd dogsled
    user@arch:~$ conda env create -f environment.yml



Next, in your Python code, import dogsled and specify the folder in which the slides are located (:code:`source_path`), the folder which should contain the normalised slides (:code:`norm_path`) and the names of the slides to be normalised (:code:`slide_names`):

 .. code-block:: python

    >>> from dogsled.normaliser import NormaliseSlides
    >>> normaliser = NormaliseSlides(source_path = '/Users/uname/slides/',
    ...                              norm_path = '/Users/uname/slides/normalised',
    ...                              slide_names = 'CMU-1-Small-Region.svs')

Double check if everything is correct:

.. code-block:: python

    >>> normaliser.slide_paths

Rev up your engines and start normalisation!

.. code-block:: python

    >>> normaliser.start()

Now dogsled will normalise the slide, save the corresponding JPEGs in the specified folder and additionally generate the thumbnails of the pre-normalised slide and of the normalised image (with a :code:`thumbnail_` prefix)

.. code-block:: shell-session

    user@arch:~$ cd /Users/uname/slides/normalised
    user@arch:normalised$ ls -1
    norm_SAS_21883_001.jpeg
    thumbnail_norm_SAS_21883_001.jpeg
    thumbnail_SAS_21883_001.jpeg


.. note::

    Depending on your requirements and installation method, you may need to install `QuPath <https://qupath.github.io/>`_ as well. Please see `installation <installation.html>`__ for further details.