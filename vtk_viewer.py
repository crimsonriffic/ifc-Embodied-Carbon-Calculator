import vtk
import sys

def render_3d_model(input_path, output_path):
    # Reader for `.stl` files (replace with appropriate reader for your format)
    reader = vtk.vtkSTLReader()
    reader.SetFileName(input_path)

    # Mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    # Actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    # Renderer
    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(1, 1, 1)  # White background

    # Add light source
    light = vtk.vtkLight()
    light.SetPosition(1, 1, 1)
    light.SetFocalPoint(0, 0, 0)
    renderer.AddLight(light)

    # Automatically position the camera
    renderer.ResetCamera()

    # Render Window
    render_window = vtk.vtkRenderWindow()
    render_window.SetOffScreenRendering(1)
    render_window.AddRenderer(renderer)

    # Window to Image Filter
    window_to_image = vtk.vtkWindowToImageFilter()
    window_to_image.SetInput(render_window)
    window_to_image.Update()

    # PNG Writer
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(output_path)
    writer.SetInputConnection(window_to_image.GetOutputPort())
    writer.Write()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python vtk_viewer.py <input_path> <output_path>")
        sys.exit(1)
        
    cube = vtk.vtkCubeSource()
    cube.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cube.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    renderer.AddActor(actor)
    renderer.ResetCamera()

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    render_3d_model(input_path, output_path)
