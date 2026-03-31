from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import rclpy


def main():
    rclpy.init()
    navigator = BasicNavigator() # 节点
    navigator.waitUntilNav2Active() # 等待导航可用


    goal_pose = PoseStamped()
    goal_pose.header.frame_id = 'map'
    goal_pose.header.stamp = navigator.get_clock().now().to_msg()
    goal_pose.pose.position.x = 2.0
    goal_pose.pose.position.y = 1.0
    goal_pose.pose.orientation.w = 1.0
    navigator.goToPose(goal_pose)
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        navigator.get_logger().info(f'remaining_distance: {feedback.distance_remaining}')
        # navigator.cancelTask()
    result = navigator.getResult()
    navigator.get_logger().info(f'navigation_result: {result}')

    # rclpy.spin(navigator)
    # rclpy.shutdown()