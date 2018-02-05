# vtkSnap
A simple, command-line image render and snaphot tool for NIFTI files

I was trying to make some nice rendered brain images for a paper and started using ITK Snap (https://github.com/pyushkevich/itksnap), which is a great tool if you have just a few images you want to render. Unfortunately, with many images it becomes a pain to load the main image, the segmentation image, rotate to the desired angle and then create the snapshot. 

This is a little tool to make all that easier. It uses VTK (VTK-8.1.0 in particular). You have to download and install VTK first (via cmake and make), then use the vtkpython executable that is created in VTK_DIR/build/bin.


There is only one Python file you need: vtkSnap.py is the help for it:

******************************************************************
usage: vtkSnap.py [-h] [--Xrot X_ROT] [--Yrot Y_ROT] [--Zrot Z_ROT]
                  in_file label_file out_file

VTK Snap: A simple VTK based snapshot tool. Uses VTK python library (built
using VTK 8.1.0).

positional arguments:
  in_file       NIFTI input filename
  label_file    File with mapping from label to RGB. CSV file with header:
                label,red,green,blue
  out_file      PNG snapshot filename

optional arguments:
  -h, --help    show this help message and exit
  --Xrot X_ROT  X rotation (degrees)
  --Yrot Y_ROT  Y rotation (degrees)
  --Zrot Z_ROT  Z rotation (degrees)

Example call: vtkpython vtkSnap.py --Xrot 90 --Yrot 90 --Zrot 185 in.nii
labels.csv out.png
******************************************************************


I've included an example nii file called example.nii along with a label file called labels_rgb_7levels.csv, so an example call would be:

vtkpython vtkSnap.py --Xrot 90 --Yrot 90 --Zrot 185 example.nii labels_rgb_7levels.csv out.png

You should be able to generate the out.png I've included.


