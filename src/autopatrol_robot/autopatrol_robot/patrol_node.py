import rclpy
from geometry_msgs.msg import PoseStamped, Pose
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.node import Node
from tf2_ros import TransformListener, Buffer
from tf_transformations import euler_from_quaternion,quaternion_from_euler # quaternion from euler
from rclpy.duration import Duration
import math #角度转弧度
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image # msg interface
from cv_bridge import CvBridge # Images type translation
import cv2 # save images

class PatrolNode(BasicNavigator):
    def __init__(self):
        super().__init__()
        # declare parameter
        self.declare_parameter('initial_point',[0.0, 0.0, 0.0])
        self.declare_parameter('target_points',[0.0, 0.0, 0.0, 1.0, 1.0, 1.57])
        self.declare_parameter('img_save_path','/home/eiche/YXros/chapter7/chap7_ws/patrol_images')
        self.initial_point_ = self.get_parameter('initial_point').value
        self.target_points_ = self.get_parameter('target_points').value
        self.img_save_path_ = self.get_parameter('img_save_path').value
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.cv_bridge_ = CvBridge()
        self.latest_img_ = None
        self.img_sub_ = self.create_subscription(Image,'/camera_sensor/image_raw',self.img_callback,qos_profile_sensor_data)
       
    def img_callback(self,msg):
        self.latest_img_ = msg

    def record_img(self,):
        if self.latest_img_ is not None:
            pose = self.get_current_pose()
            cv_image = self.cv_bridge_.imgmsg_to_cv2(self.latest_img_)
            path = f'{self.img_save_path_}/img_{pose.translation.x:3.2f}_{pose.translation.y:3.2f}.png'
            cv2.imwrite(path,cv_image)

    def get_pose_by_xyyaw(self, x, y, yaw):
        """
        return PoseStamped object
        """
        pose = PoseStamped()
        pose.header.frame_id = "map"
        pose.pose.position.x = x
        pose.pose.position.y = y
        # quaternion order: xyzw
        quat = quaternion_from_euler(0,0,yaw)
        pose.pose.orientation.x = quat[0]
        pose.pose.orientation.y = quat[1]
        pose.pose.orientation.z = quat[2]
        pose.pose.orientation.w = quat[3]
        return pose


    def init_robot_pose(self):
        """
        initialize robot pose
        """
        self.initial_point_ = self.get_parameter('initial_point').value
        init_pose = self.get_pose_by_xyyaw(self.initial_point_[0],self.initial_point_[1],self.initial_point_[2])
        self.setInitialPose(init_pose)
        self.waitUntilNav2Active() # wait until Nav2 is active


    def get_target_points(self):
        """
        get target points from parameters
        """
        points = []
        self.target_points_ = self.get_parameter('target_points').value
        for index in range(int(len(self.target_points_)/3)):
            x = self.target_points_[index*3]
            y = self.target_points_[index*3+1]
            yaw = self.target_points_[index*3+2]
            points.append([x,y,yaw])
            self.get_logger().info(f"Target point {index}: ({x}, {y}, {yaw})")
        return points

    def nav_to_pose(self,target_point):
        """
        navigate to target pose
        """
        self.waitUntilNav2Active()
        self.goToPose(target_point)
        while not self.isTaskComplete():
            feedback = self.getFeedback()
            if feedback:
                self.get_logger().info(
                    f'Remaining distance: {feedback.distance_remaining}')

        result = self.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info('Navigation result: succeeded')
        elif result == TaskResult.CANCELED:
            self.get_logger().warn('Navigation result: canceled')
        elif result == TaskResult.FAILED:
            self.get_logger().error('Navigation result: failed')
        else:
            self.get_logger().error('Navigation result: invalid status')

    def get_current_pose(self):
        """
        get current robot pose
        """
        while rclpy.ok():
            try:
                tf = self.buffer.lookup_transform(
                    'map', 'base_footprint', rclpy.time.Time(seconds=0), rclpy.time.Duration(seconds=1))
                transform = tf.transform
                rotation_euler = euler_from_quaternion([
                    transform.rotation.x,
                    transform.rotation.y,
                    transform.rotation.z,
                    transform.rotation.w
                ])
                self.get_logger().info(
                    f'Current translation: {transform.translation}')
                return transform
            except Exception as e:
                self.get_logger().warn(f'Failed to get transform: {str(e)}')



def main():
    rclpy.init()
    patrol = PatrolNode() # node
    patrol.init_robot_pose()
   
    while rclpy.ok():
        points = patrol.get_target_points()
        for point in points:
            x,y,yaw = point[0],point[1],point[2]
            target_pose = patrol.get_pose_by_xyyaw(x,y,yaw)
            patrol.nav_to_pose(target_pose)
            patrol.record_img()
    
    rclpy.shutdown()