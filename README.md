<img src="https://github.com/RhDm/dogsled/blob/main/docs/source/_static/dogsled_logo.svg" width="300">

<br>

[![tests workflow](https://github.com/RhDm/dogsled/actions/workflows/main.yml/badge.svg)](https://github.com/RhDm/dogsled/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/RhDm/dogsled/branch/main/graph/badge.svg?token=IE4K5V5FGW)](https://codecov.io/gh/RhDm/dogsled)

<br>

`dogsled` is an open-source Python package that does only one thing: Macenko [1] stain normalisation of large medical slides readable by OpenSlide. It generates either JPEG or TIFF normalised image


Why *dogsled*? Well, first of all, because of the dogs. Second, because together many dogs can push a cargo too heavy for one dog to handle. Similarily, dogsled divides heavy computations into smaller ones. As with many algorithms and life situations, divide and conquer, right?

## Quirks and features

Currently, `dogsled` can:
- normalise all slides located in a specified folder
- normalise slides specified by name
- normalise slides defined in a QuPath library (either all or the ones specified by name and/or index)
- generate JPEG equivalents of the normalised slides
- generate TIFF equivalents of the normalised slides (also for large slides not fitting in RAM)
- create hematoxylin/eosin decoupled normalised images
- create thumbnails of all slides (pre-normalised and normalised)

## Documentation
`dogsled` about page, quickstart, installation and API can be found at [dogsled.readthedocs.io](LINK_HERE)

<br>

<img src="https://github.com/RhDm/dogsled/blob/main/docs/source/_static/graph.jpeg" width="800">

<br>

[1] M. Macenko, M. Niethammer, J. S. Marron, D. Borland, J. T. Woosley, Guan Xiaojun, C. Schmitt, and N. E. Thomas. A method for normalizing histology slides for quantitative analysis. In 2009 IEEE International Symposium on Biomedical Imaging: From Nano to Macro, 1107–1110. 2009. doi:10.1109/ISBI.2009.5193250.
