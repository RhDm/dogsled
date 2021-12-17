Installation
=====================================


Using :code:`environment.yml` file
'''''''''''''''''''''''''''''''''''''

Currently, the fastest and easiest way to install dogsled is via Conda using the YML file located in
the dogsled GitHub repository. For Linux and macOS:

.. code-block:: console

    user@arch:~$ git clone https://github.com/RhDm/dogsled.git
    user@arch:~$ cd dogsled
    user@arch:~$ conda env create -f environment.yml
    user@arch:~$ conda activate dogsled

for Windows in the same way but with a different YML file:

.. code-block:: console

    user@arch:~$ conda env create -f win_environment.yml

This method installs autocamically all dependencies including `libvips <https://www.libvips.org/>`_.

Via pip
'''''''''''''''''''''''''''''''''''''

dogsled can be installed also via pip (be sure to have Python 3.9 on your system and create a separate environment using, for example, `virtuelenv <https://virtualenv.pypa.io/en/latest/index.html/>`_):

.. code-block:: console

    user@arch:~$ pip install virtualenv
    user@arch:~$ virtualenv /PATH/WHERE/PYTHON/ENV/WILL/LIVE --python=python3.9
    user@arch:~$ source /PATH/WHERE/PYTHON/ENV/WILL/LIVE/bin/activate
    user@arch:~$ pip install dogsled

This, however, will not install libvips on Linux and macOS, please follow the `installation guides <https://www.libvips.org/install.html/>`_.


As dogsled uses Bayer's :py:mod:`paquo` library for interactions with QuPath files, `QuPath <https://qupath.github.io/>`_ installation is also required if you install dogsled via pip (QuPath is automatically installed if Conda is used)


In case you plan to work with large slides (over 100,000pixels per side), or if your system can not handle
smaller slide sizes causing a crash, you might want to set :py:mod:`vips_stitcher` key value of the :py:attr:`DEFAULTS`
dictionary to :py:attr:`True`, see `API <api.html#confval-prefer_vips>`__ for further details.





