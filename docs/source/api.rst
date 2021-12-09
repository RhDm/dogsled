API
=====================================
.. role:: strike
    :class: strike

The :class:`NormaliseSlides` class
=====================================

:class:`NormaliseSlides` class
'''''''''''''''''''''''''''''''''''''

.. code-block:: python

    dogsled.normaliser.NormaliseSlides

:class:`NormaliseSlides` is the main interface for slide normalisation. It is required to specify which folder should contain the normalised slides by passing the :py:attr:`norm_path` argument. The slides themselves can be specified either by passing the :py:attr:`qpproj_path` or :py:attr:`svs_path`. If both are specified, then :py:attr:`qpproj_path` is used and the :py:attr:`svs_path` is ignored. See :meth:`__init__` for further details:


.. autoclass:: dogsled.normaliser.NormaliseSlides
   :members: __init__

Example usage:

.. code-block:: python

    from dogsled.normaliser import NormaliseSlides

    normaliser = NormaliseSlides(norm_path = '/Users/uname/slides/normalised',
                                 svs_path = '/Users/uname/slides/',
                                 qpproj_path = '/Users/uname/QuPath_projects/project.qpproj',
                                 slides_indexes = [0,1,8],
                                 slide_names = ['SAS_21883_001.svs', 'VUHSK_1912.svs'])

.. note::

    It is possible to specify both the names and the indexes of the slides in the QuPath project. In case of an overlap, the slide normalisation will not be repeated

As the normalisation may take a significant amount of time, it is best to double-check whether all specified parameters are correct before proceeding further. This can be done by examining the output of the

.. code-block:: python

    normaliser.file_data

this will show the location of the QuPath project, path to the pre- and normalised slides, temporary folder path, indexes of the selected slides and the names of the slide files which will be normalised

Once the instance of the :class:`NormaliseSlides` is created and the arguments controlled, the normalisation can be started using :meth:`start()` method:

.. code-block:: python

    normaliser.start()

This method does not require any arguments. During normalisation, dogsled will provide the basic progress information, e.g.:

.. code-block:: console

    12/06/2021 09:08:48 PM normaliser INFO: [ Slide 1/2 SAS_21883_001.svs tile 1/4 reading slide sector ]

The status information includes the number of the current slide and the total number of the slides to be normalised (`1/2`), name of the currently processed slide, which tile is currently normalised and in how many tiles the slide will be processed (`1/4`), which operation is currently in progress (`reading slide sector`).

:meth:`repeat_stitching` method
'''''''''''''''''''''''''''''''''''''
When big slides are handled, many normalised tiles can be produced. These tiles are later stitched together, producing the end result- a normalised image. In case this stitching caused the system to crash, it is possible to repeat it using the :meth:`repeat_stitching` method. To confirm that stitching has caused the crash and repeated stitching is applicable, navigate to the :py:attr:`norm_path` and check the last lines of the log file:

.. code-block:: console

    user@arch:~$ cd /Users/uname/slides/normalised
    user@arch:normalised$ tail -3 dogsled.log
    01/12/2021 09:16:50 PM normaliser INFO: [ Slide 1/1 SAS_21883_001.svs tile 4/4 stitching image together ]
    01/12/2021 09:16:50 PM normaliser INFO: [ Slide 1/1 SAS_21883_001.svs tile 4/4 stitching using PIL ]
    01/12/2021 09:16:50 PM normaliser INFO: [ Slide 1/1 SAS_21883_001.svs tile 4/4 stitching slide: SAS_21883_001.svs ]
    01/12/2021 09:16:50 PM normaliser INFO: [ Slide 1/1 SAS_21883_001.svs tile 4/4 stitching finished ]
    01/12/2021 09:16:50 PM normaliser INFO: [ Slide 1/1 SAS_21883_001.svs tile 4/4 saving jpeg image: norm_SAS_21883_001 ]

If the last logged event states the name of the stitched slide or the status of saving image (last three lanes in the above example), the stitching might have caused a crash, and re-stitching can be applied (also, you might want to check whether the temporary folder of the slide contains a correct number of tiles, 4 in case of the example above). For this purpose, :class:`NormaliseSlides` has to be reinitialised prior repeating the stitching using **only** the slide which caused the crash. Also, it is recommended to use VIPS instead of the default PIL for slide stitching and saving, as it minimises the risk of a crash:

.. code-block:: python

    from dogsled.normaliser import NormaliseSlides
    from dogsled.defaults import DEFAULTS

    normaliser = NormaliseSlides(norm_path = '/Users/uname/slides/normalised',
                                 svs_path = '/Users/uname/slides/',
                                 qpproj_path = '/Users/uname/QuPath_projects/project.qpproj',
                                 slide_names = ['SAS_21883_001.svs'])
    DEFAULTS['prefer_vips']= True
    normaliser.repeat_stitching()

.. note::

    dogseld is designed to avoid crashes. When the :class:`NormaliseSlides` is initialised, it analyses the RAM available and tailors the size of the tiles accordingly. The thresholds are defined in the :py:attr:`DEFAULTS` dictionary (see further). Apart from that, dogsled gives a (very) aproximate estimation of the space required for normalisation of the selected slides and the space available (the normalisation will be started regardless of the space estimation results). Both, RAM and space estimation information are shown during the :class:`NormaliseSlides` initialisation



The :py:attr:`DEFAULTS` dictionary
=====================================


.. code-block:: python

    dogsled.defaults.DEFAULTS

This dictionary holds constants used for normalisation and some other normalisation parameters.

.. code-block:: python

    import numpy as np

    DEFAULTS = {'show_results': False,
                'ram_megapixel': {8000: 12000, 8001: 24500},
                'output_type': ['norm'],
                'dtype': np.float16,
                'temporary_folder_name': 'dogsled_temp',
                'remove_temporary_files': False,
                'jpeg_quality': 95,
                'vips_tiff_compression': 'lzw',
                'PIL_MAX_IMAGE_PIXELS': 2000000000,
                'thumbnail': True,
                'thumbnail_max_side': 6000,
                'prefer_vips': False,
                'OpenSlide_formats': ['.svs', '.tif', '.tiff', '.scn', '.vms', '.vmu', '.ndpi', '.mrxs', '.svslide', '.bif'],
                'first_tile': 'middle',
                # normalisation constants:
                'normalising_c': 255,
                'alpha': 0.0001,
                'beta': 0.0015,
                'he_ref': array([[0.6895, 0.1759],
                                 [0.6973, 0.8286],
                                 [0.674 , 0.5312]], dtype=float16),
                'max_s_ref': array([0.498, 0.927], dtype=float16)}

All of the parameters may be re-defined by the user prior :class:`NormaliseSlides` initialisation:

.. code-block:: python

    from dogsled.normaliser import NormaliseSlides
    from dogsled.defaults import DEFAULTS

    DEFAULTS['output_type'] = ['norm', 'he', 'eo']
    DEFAULTS['prefer_vips'] = True

    normaliser = NormaliseSlides(svs_path = '/Users/uname/slides/',
                                 qpproj_path = '/Users/uname/QuPath_projects/project.qpproj',
                                 slides_indexes = [0,1,8],
                                 slide_names = ['SAS_21883_001.svs', 'VUHSK_1912.svs'])

    normaliser.start()


.. confval:: ram_megapixel

    :attr:`ram_megapixel` is a mapping of available RAM to the tile size that will
    be used during normalisation. During initialisation, dogsled checks available RAM using
    :py:attr:`psutil`. If the value is less than or equal 8000MB, then the maximum width and height
    of the tile used are set to 12000px; if the value is bigger- 24500

    :type: dictionary
    :default: :py:attr:`{8000: 12000, 8001: 24500}`

.. confval:: output_type

    As the Macenko normalisation gives access to the stain-decoupling, dogsled can
    generate the hematoxylin and eosin images in addition to the normalised image. If
    these images are needed, they can be specified using :py:attr:`['he', 'eo']` list.
    E.g. for all three, specify :py:attr:`['norm', 'he', 'eo']`

    :type: list[string]
    :default: :py:attr:`['norm']`

.. confval:: dtype

    NumPy data type used when performing the normalisation operations

    :type: list[string]
    :default: :py:attr:`np.float16`

.. confval:: temporary_folder_name

    Name of the temporary folder which is created inside the :py:attr:`norm_path` and will hold
    the normalised slide tiles

    :type: string
    :default: :py:attr:`'dogsled_temp'`

.. confval:: remove_temporary_files

    Whether the normalised slide tiles stored in the temporary folder should be removed after
    normalisation. It may be set to :py:attr:`False` if subsequent tile processing is required by
    the user. If set to  :py:attr:`True`, before deleting dogsled checks whether the normalised
    slide was indeed stitched together

    .. note::

        The normalised slide tiles will be removed; however, the temporary folders themselves are
        kept

    :type: boolean
    :default: :py:attr:`True`

.. confval:: jpeg_quality

    `JPEG quality <https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#jpeg/>`_ used when creating the tiles

    :type: integer
    :default: :py:attr:`95`

.. confval:: prefer_vips

    If large slides are handled, their tiles might not fit into the memory at once when stitched
    together (e.g. slides with 40x magnification and size over 100,000pixels per side). In these cases,
    it is possible to stitch the tiles together using sequential read. This is done using libvips/pyvips,
    which is disabled by default. Please see [INSTALLATION] on how to install libvips

    .. attention::

        When vips is used for stitching, the normalised slide will be saved as TIFF file. It is recommended
        to use vips/openslide for further processing of this normalised mage. Also, this TIFF file will
        contain spoofed metadata and can be opened with QuPath

    :type: boolean
    :default: :py:attr:`False`

.. confval:: vips_tiff_compression

    Sets the TIFF compression. See `pyvips manual <https://libvips.github.io/pyvips/enums.html#pyvips.enums.ForeignTiffCompression/>`_ for other options

    :type: string
    :default: :py:attr:`'lzw'`

.. confval:: PIL_MAX_IMAGE_PIXELS

    sets the :py:mod:`PIL`'s :py:attr:`Image.MAX_IMAGE_PIXELS` flag to a higher value, as PIL will fire :py:exc:`DecompressionBombError`
    otherwise

    :type: integer
    :default: :py:attr:`2000000000`

.. confval:: thumbnail

    Whether the thumbnails of the pre- and normalised images should be generated

    :type: boolean
    :default: :py:attr:`true`

.. confval:: thumbnail_max_side

    Maximum side of the generated tile. E.g. if set to 6000px and the source slide has dimensions of
    12,000x18,000px, the resulting thumbnail will have dimensions of 4,000x6,000px

    :type: integer
    :default: :py:attr:`6000`

.. confval:: OpenSlide_formats

    List of the slide `formats <https://openslide.org/#about-openslide/>`_ which can be handled using OpenSlide and thus by dogsled as well

    :type: list[string]
    :default: :py:attr:`['.svs', '.tif', '.tiff', '.scn', '.vms', '.vmu', '.ndpi', '.mrxs', '.svslide', '.bif']`

.. confval:: first_tile

    When the slide is processed in tiles, the first normalised tile is used for estimating the slide-specific
    parameters. However, if the tile in the left upper corner (the first one, if ordered from left to right,
    top to bottom) contains only background, these parameters are estimated incorrectly, leading to the normalised
    slide having wrong colours. Therefore, the tile located in the centre of the slide is normalised first. As
    an alternative, an :py:attr:`int` may be provided indicating the number of the tile processed first

    :type: string
    :default: :py:attr:`'middle'`

.. confval:: normalising_c, alpha, beta, he_ref, max_s_ref

    Macenko normalisation constants

    :type: integer, float, float, np.array, np.array
    :default: :py:attr:`255, 0.001, 0.0015, array([[0.6895, 0.1759],
                             [0.6973, 0.8286],
                             [0.674 , 0.5312]], dtype=float16), array([0.498, 0.927], dtype=float16)`
