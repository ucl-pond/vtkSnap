#!/usr/bin/env python
import numpy as np

import vtk
from vtk.util.misc import vtkGetDataRoot
from vtk.util.misc import vtkGetTempDir

import argparse

parser			= argparse.ArgumentParser(
							description="VTK Snap: A simple VTK based snapshot tool. Uses VTK python library (built using VTK 8.1.0).",
							epilog='Example call: vtkpython vtkSnap.py --Xrot 90 --Yrot 90 --Zrot 185 in.nii labels.csv out.png' )
parser.add_argument('in_file', 		help='NIFTI input filename')
parser.add_argument('label_file', 	help='File with mapping from label to RGB. CSV file with header: label,red,green,blue')
parser.add_argument('out_file', 	help='PNG snapshot filename')
parser.add_argument('--Xrot', 		dest='x_rot', type = float, default = 0, help='X rotation (degrees)')
parser.add_argument('--Yrot', 		dest='y_rot', type = float, default = 0, help='Y rotation (degrees)')
parser.add_argument('--Zrot', 		dest='z_rot', type = float, default = 0, help='Z rotation (degrees)')

args 			= parser.parse_args()

print 'Rotation x: {} y: {} z: {}'.format(args.x_rot, args.y_rot, args.z_rot)
#print("Rotation: str(args.x_rot) + " " + str(args.y_rot) + " " + str(args.z_rot))
#print(args.echo())

#************ READ THE RGB LABEL MAP
import csv
rgbDict					= {}
rgbFilename 			= args.label_file; 	#"/Users/leonaksman/Desktop/pythonVTK/labels_rgb_7levels.csv"
with open(rgbFilename) as f:
	reader 					= csv.DictReader(f)
	for row in reader:
		vec_i 			= np.array([float(row['red']), float(row['green']), float(row['blue'])])
		rgbDict[int(row['label'])] = vec_i

inNiftiFilename 		= args.in_file; 	#"/Users/leonaksman/Desktop/pythonVTK/amyloid_l.nii"
outSnapshotFilename 	= args.out_file;	# "/Users/leonaksman/Desktop/pythonVTK/screenshot.png"


#********** Create the Renderer, RenderWindow and Camera
ren 				= vtk.vtkRenderer()
renWin 				= vtk.vtkRenderWindow()
renWin.AddRenderer(ren)


# ************* Read the NIFTI file
reader 			= vtk.vtkNIFTIImageReader()
reader.SetFileName(inNiftiFilename)
reader.Update()

imageData 		= reader.GetOutput() #vtkImageData type

MARCHING_CUBES_THRESHOLD = 0.01

#************* GET CENTER OF MASS OF WHOLE STRUCTURE SO WE CAN TRANSLATE PARTS
#Run marching cubes on the whole input image
fltMarching_whole 	= vtk.vtkMarchingCubes();   #***** Discrete version instead?
fltMarching_whole.SetInputData(imageData) 
fltMarching_whole.ComputeScalarsOff();
fltMarching_whole.ComputeGradientsOff();
fltMarching_whole.ComputeNormalsOn();
fltMarching_whole.SetNumberOfContours(1);
fltMarching_whole.SetValue(0, MARCHING_CUBES_THRESHOLD);
fltMarching_whole.Update();

centerFilter 		= vtk.vtkCenterOfMass()
centerFilter.SetInputConnection(fltMarching_whole.GetOutputPort())
centerFilter.SetUseScalarsAsWeights(False)
centerFilter.Update()
center 				= centerFilter.GetCenter()
transform 			= vtk.vtkTransform()
transform.PostMultiply()
transform.Translate(-center[0], -center[1], -center[2])
transform.RotateWXYZ(args.x_rot, 1, 0, 0)
transform.RotateWXYZ(args.y_rot, 0, 1, 0) 
transform.RotateWXYZ(args.z_rot, 0, 0, 1)


#************** GET RANGE OF LABELS
imageScalars 	= imageData.GetPointData().GetScalars()
iMin, iMax 		= imageScalars.GetValueRange()
assert iMin == 0

print 'Image has label range: {} to {}.'.format(iMin, iMax)

# ************* Run marching cubes on each unique label, add actor
for i in range(1, iMax + 1): #imageScalars: #

	if i == 0:
		continue

 	print("Processing label " + str(i));
	assert i in rgbDict.keys(), "Label {} not in labels file".format(i) 


	#imageData_i = imageData;
	imageData_i = vtk.vtkImageData();
	imageData_i.DeepCopy(imageData);

	#******** FAST VERSION
	thresh = vtk.vtkImageThreshold()
	thresh.SetInputData(imageData_i)
	thresh.ThresholdBetween (i, i)
	thresh.ReplaceInOn()
	thresh.ReplaceOutOn()
	thresh.SetInValue(i)
	thresh.SetOutValue(0)
	thresh.Update()
	
	#******** Check current label exists in image
	iMin, iMax 	= thresh.GetOutput().GetPointData().GetScalars().GetValueRange()
	if iMin == 0 and iMax == 0:
		print("Label {} not found, skipping.".format(i))
		continue
	
	# Run marching cubes on the input image
	fltMarching_i 		= vtk.vtkMarchingCubes();   #***** Discrete version instead?
	fltMarching_i.SetInputData(thresh.GetOutput()) 
	fltMarching_i.ComputeScalarsOff();
	fltMarching_i.ComputeGradientsOff();
	fltMarching_i.ComputeNormalsOn();
	fltMarching_i.SetNumberOfContours(1);
	fltMarching_i.SetValue(0, MARCHING_CUBES_THRESHOLD);
	fltMarching_i.Update();

# 	#**************** SMOOTHING
	smoother_i 			= vtk.vtkWindowedSincPolyDataFilter()
	smoother_i.SetInputConnection(fltMarching_i.GetOutputPort());
 	smoother_i.SetNumberOfIterations(50)
 	smoother_i.BoundarySmoothingOff();
 	smoother_i.FeatureEdgeSmoothingOff();
	smoother_i.SetFeatureAngle(45) 		#120);
	smoother_i.SetPassBand(0.1) 		#0.001);
 	smoother_i.NonManifoldSmoothingOn();
 	smoother_i.NormalizeCoordinatesOn();
 	smoother_i.Update();
	normals_i 			= vtk.vtkPolyDataNormals()
	normals_i.SetInputConnection(smoother_i.GetOutputPort())
	normals_i.FlipNormalsOn()
	
	#**************** CENTERING
	transFilter_i 		= vtk.vtkTransformFilter()
	transFilter_i.SetInputConnection(normals_i.GetOutputPort()) 
	transFilter_i.SetTransform(transform)
	
	# ********** Create the mapper and actor, add with a specific color
	franMapper_i 		= vtk.vtkPolyDataMapper()
	franMapper_i.SetInputConnection(transFilter_i.GetOutputPort()) #normals_i
	franMapper_i.SetScalarModeToUseCellData()
	franMapper_i.ScalarVisibilityOn()
	franMapper_i.Update()    

	# ********* Add the actors to the renderer, set the background and size
	franActor_i 		= vtk.vtkActor()
	franActor_i.SetMapper(franMapper_i)

	# ********* Color from RGB dictionary
	#get rgb vector for this label from dictionary
	assert i in rgbDict
	rgb_vec 			= rgbDict[i]
	if np.where(rgb_vec > 1):
		rgb_vec 		= rgb_vec / 255
	franActor_i.GetProperty().SetColor(rgb_vec[0], rgb_vec[1], rgb_vec[2])
	
	ren.AddActor(franActor_i)


#******** ADDED ALL ACTORS -> RENDER
cam1 				= vtk.vtkCamera()
cam1.SetFocalPoint(0, 0, 0);
cam1.SetPosition(0, 0, 400);
ren.SetActiveCamera(cam1)

ren.SetBackground(1, 1, 1)
renWin.SetSize(1500, 1500)
renWin.Render()

# **************** screenshot code:
w2if 				= vtk.vtkWindowToImageFilter()
w2if.SetInput(renWin)

w2if.Update()
writer 				= vtk.vtkPNGWriter()
writer.SetFileName(outSnapshotFilename)
writer.SetInputData(w2if.GetOutput())
writer.Write()
print("Wrote snapshot to " + outSnapshotFilename)

#start the render window interactor
#iren 				= vtk.vtkRenderWindowInteractor()
#iren.SetRenderWindow(renWin)
#iren.Start()

