"""Optional ROS 2 `std_msgs/String` publisher; not a motor safety controller."""
def publish_once(decision,topic='/semantic_robot/decision'):
    try:
        import rclpy
        from rclpy.node import Node
        from std_msgs.msg import String
    except ImportError as e:
        raise RuntimeError('Requires separately installed ROS 2 rclpy and std_msgs') from e
    rclpy.init()
    try:
        node=Node('semantic_decision_demo')
        pub=node.create_publisher(String,topic,10)
        msg=String();msg.data=decision
        pub.publish(msg)
        rclpy.spin_once(node,timeout_sec=.2)
        node.destroy_node()
    finally:rclpy.shutdown()
