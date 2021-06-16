import open3d as o3d
import os
import glob
import argparse
import time
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--root_dir', type=str,
                    help='root directory where visualization results save')
parser.add_argument('--tracklet_num', type=int,
                    default=1, help='number of tracklet')
args = parser.parse_args()


"""
There are 4 files for each frame, including the point cloud of the scene, the GT box of the target, the predicted box of P2B and the predicted box of BAT;
Note: At the beginning of each sequence, we have frame 0 which contains only 2 files - the point cloud of the scene and the first GT target BB.

Here is an example of the first frame of sequence 05:

tracklet0005-case0001-search.xyz
tracklet0005-case0001-gt_box.obj
tracklet0005-case0001-box.obj
tracklet0005-case0001-box_p2b.obj

"""
name_str = 'tracklet%04d-case%04d-%s'
objects = sorted(glob.glob(os.path.join(
    args.root_dir, 'tracklet%04d*' % args.tracklet_num)))

# There are only 2 files for frame 0
num_frame = (len(objects) - 2) // 4
print('num of frames: ', num_frame)

colors_1 = np.array([192 / 255, 0, 0])
colors_2 = np.array([111 / 255, 31 / 255, 231 / 255])
colors_3 = np.array([73 / 255, 159 / 255, 128 / 255])
colors = [colors_1, colors_2, colors_3]

# load files
obj_list = []
for obj in objects:
    # load point clouds
    if obj.endswith('xyz'):
        point_obj = o3d.io.read_point_cloud(obj)
        point_np = np.asarray(point_obj.points)
        points_colors = np.ones_like(point_np) * 0.5
        point_obj.colors = o3d.utility.Vector3dVector(points_colors)

        obj_list.append(point_obj)

    # load boxes
    else:

        bb = o3d.io.read_triangle_mesh(obj).get_oriented_bounding_box()
        line_set = o3d.geometry.LineSet.create_from_oriented_bounding_box(bb)

        # uncomment the following two lines to reproduce the buggy results.
        # bb = o3d.io.read_triangle_mesh(obj).get_axis_aligned_bounding_box()
        # line_set = o3d.geometry.LineSet.create_from_axis_aligned_bounding_box(bb)

        if 'p2b' in obj:
            line_set.paint_uniform_color(colors[1])
        elif 'gt' in obj:
            line_set.paint_uniform_color(colors[2])
        else:
            line_set.paint_uniform_color(colors[0])

        obj_list.append(line_set)


i = 0

def callback_next(vis):
    global i

    i += 1
    vis.clear_geometries()
    print(i)
    for obj in obj_list[i * 4 + 2:i * 4 + 4 + 2]:
        vis.add_geometry(obj, reset_bounding_box=False)

    return False


def callback_prev(vis):
    global i
    if i - 1 < 0:
        return False
    i -= 1

    print(i)
    vis.clear_geometries()
    if i == 0:
        for obj in obj_list[0:2]:
            vis.add_geometry(obj, reset_bounding_box=False)
        return False

    for obj in obj_list[i * 4 + 2:i * 4 + 4 + 2]:
        vis.add_geometry(obj, reset_bounding_box=False)
    return False


o3d.visualization.draw_geometries_with_key_callbacks(
    obj_list[:2], {ord('K'): callback_next, ord('J'): callback_prev})
