from typing import List
import math

# Draws a line between point_1 and point_2
# name creates the node in the tree so we just update the same node each time
def draw_line(
    robot,
    line_map,
    name: str,
    point_1: List[float],
    point_2: List[float],
    color_rgb: List[float],
):
    # Create node with name if it doesn't exist yet
    node_name = f"LINE_{name}"

    if node_name not in line_map:
        root_node = robot.getRoot()
        root_children_field = root_node.getField("children")

        template = (
            f"DEF {node_name} "
            + """Shape {
            appearance Appearance {
                material Material {
                    emissiveColor """
            + " ".join(map(str, color_rgb))
            + """
                }
            }
            geometry DEF TRAIL_LINE_SET IndexedLineSet {
                coord Coordinate {
                    point [
                        0 0 0
                        0 0 0
                    ]
                }
                coordIndex [
                    0 1 -1
                ]
            }
        }"""
        )
        root_children_field.importMFNodeFromString(-1, template)

        # Update the coords based on points
        trail_set_node = robot.getFromDef(f"{node_name}.TRAIL_LINE_SET")
        coordinates_node = trail_set_node.getField("coord").getSFNode()
        point_field = coordinates_node.getField("point")
        line_map[node_name] = point_field
    else:
        point_field = line_map[node_name]

    point_field.setMFVec3f(0, point_1)
    point_field.setMFVec3f(1, point_2)


# Draws a line between point_1 and point_2
# name creates the node in the tree so we just update the same node each time
def draw_arrow(
    robot,
    line_map,
    name: str,
    point_1: List[float],
    point_2: List[float],
    color_rgb: List[float],
    arrow_angle_deg=35,
    arrow_len_ratio=0.25,
):
    # Create node with name if it doesn't exist yet
    node_name = f"ARROW_{name}"

    if node_name not in line_map:
        root_node = robot.getRoot()
        root_children_field = root_node.getField("children")

        template = (
            f"DEF {node_name} "
            + """Shape {
            appearance Appearance {
                material Material {
                    emissiveColor """
            + " ".join(map(str, color_rgb))
            + """
                }
            }
            geometry DEF TRAIL_LINE_SET IndexedLineSet {
                coord Coordinate {
                    point [
                        0 0 0
                        0 0 0
                        0 0 0
                        0 0 0
                    ]
                }
                coordIndex [
                    0 1 -1
                    1 2 -1
                    1 3 -1
                ]
            }
        }"""
        )
        root_children_field.importMFNodeFromString(-1, template)

        # Update the coords based on points
        trail_set_node = robot.getFromDef(f"{node_name}.TRAIL_LINE_SET")
        coordinates_node = trail_set_node.getField("coord").getSFNode()
        point_field = coordinates_node.getField("point")
        line_map[node_name] = point_field
    else:
        point_field = line_map[node_name]

    # calculate arrow points based on start/end
    # convert to polar
    delta = [point_1[0] - point_2[0], point_1[1] - point_2[1]]
    length = math.sqrt(delta[0] ** 2 + delta[1] ** 2)
    angle = math.atan2(delta[0], delta[1])

    left_angle = angle + math.radians(arrow_angle_deg)
    right_angle = angle - math.radians(arrow_angle_deg)

    arrow_length = length * arrow_len_ratio
    arrow_left = [
        arrow_length * math.sin(left_angle) + point_2[0],
        arrow_length * math.cos(left_angle) + point_2[1],
        point_2[2],
    ]
    arrow_right = [
        arrow_length * math.sin(right_angle) + point_2[0],
        arrow_length * math.cos(right_angle) + point_2[1],
        point_2[2],
    ]

    point_field.setMFVec3f(0, point_1)
    point_field.setMFVec3f(1, point_2)
    point_field.setMFVec3f(2, arrow_left)
    point_field.setMFVec3f(3, arrow_right)


def draw_circle(
    robot,
    line_map,
    name: str,
    center: List[float],
    color_rgb: List[float],
    radius: float,
    num_segments=20,
):
    # Create node with name if it doesn't exist yet
    node_name = f"CIRCLE_{name}"

    if node_name not in line_map:
        node = robot.getFromDef(node_name)
        root_node = robot.getRoot()
        root_children_field = root_node.getField("children")

        template = (
            f"DEF {node_name} "
            + """Shape {
            appearance Appearance {
                material Material {
                    emissiveColor """
            + " ".join(map(str, color_rgb))
            + """
                }
            }
            geometry DEF TRAIL_LINE_SET IndexedLineSet {
                coord Coordinate {
                    point [
                        """
            + ("0 0 0\n" * num_segments)
            + """
                    ]
                }
                coordIndex [
                    """
            + " ".join(map(str, range(num_segments)))
            + """ 0 -1
                ]
            }
        }"""
        )
        root_children_field.importMFNodeFromString(-1, template)
        node = robot.getFromDef(node_name)

        # Update the coords based on points
        trail_set_node = robot.getFromDef(f"{node_name}.TRAIL_LINE_SET")
        coordinates_node = trail_set_node.getField("coord").getSFNode()
        point_field = coordinates_node.getField("point")
        line_map[node_name] = point_field
    else:
        point_field = line_map[node_name]

    # Use polar coordinates to find points on the circle
    for i in range(num_segments):
        theta = math.pi * 2 / num_segments * i
        point = [
            center[0] + radius * math.cos(theta),
            center[1] + radius * math.sin(theta),
            center[2],
        ]
        point_field.setMFVec3f(i, point)
