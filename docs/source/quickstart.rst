Quick tour
=====================================
.. important::

    First things first, dogsled relies on OpenSlide for reading the slide files. Please follow OpenSlide's `installation guide <https://openslide.org/download/#distribution-packages/>`_ before proceeding.



The simplest dogsled installation can be done via pip:

.. hint::

    It is highly recommended not to install dogsled (or any other package) in the base environment, create a new one using `Conda <https://docs.conda.io/en/latest//>`__ or `venv <https://docs.python.org/3/library/venv.html/>`__

.. code-block:: console

    user@arch:~$ pip install dogsled

Next, in your Python code, import dogsled and specify the folder in which the slides are located (:code:`svs_path`), the folder which should contain the normalised slides (:code:`norm_path`) and the names of the slides to be normalised (:code:`slide_names`):

 .. code-block:: python

    >>> from dogsled.normaliser import NormaliseSlides
    >>> normaliser = NormaliseSlides(svs_path = '/Users/uname/slides/',
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

    Depending on your requirements, you may need to install `QuPath <https://qupath.github.io/>`_ and/or `libvips <https://www.libvips.org/>`_. Please see `installation <installation.html>`__ for further details.