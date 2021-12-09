Installation
=====================================

Currently, dogsled can be installed via pip:

.. code-block:: console

    user@arch:~$ pip install dogsled

Or, if you prefer an editable version:

.. code-block:: console

    user@arch:~$ git clone https://github.com/RhDm/dogsled.git
    user@arch:~$ cd dogsled
    user@arch:~$ pip install -e .

It is also possible to create a dogsled Conda environment:

.. code-block:: console

    user@arch:~$ git clone https://github.com/RhDm/dogsled.git
    user@arch:~$ cd dogsled
    user@arch:~$ conda env create -f environment.yml
    user@arch:~$ conda activate dogsled

.. note::

    When creating Conda environment and installing packages specified in environment.yml, all
    other libraries described further (OpenSlide and libvips) are installed automatically

As dogsled relies on OpenSlide, please install `OpenSlide <https://openslide.org/>`_ as well.
:py:mod:`openslide-python` will be installed automatically during dogsled installation.

`QuPath <https://qupath.github.io/>`_ installation is also required if you plan to normalise
slides of the QuPath projects. In that case, dogsled will use Bayer's excellent :py:mod:`paquo` library
for interactions with QuPath files (installed automatically together with dogsled).


In case you plan to work with large slides (over 100,000pixels per side), or if your system can not handle
smaller slide sizes causing a crash, you might want to install `libvips <https://www.libvips.org/>`_ and set
the :py:mod:`prefer_vips` of the :py:attr:`DEFAULTS` dictionary to :py:attr:`True`, see `API <api.html#confval-prefer_vips>`__
for further details.





