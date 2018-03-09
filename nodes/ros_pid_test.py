#!/usr/bin/env python

import rospy
import time
from pololu import Controller

# import message types
from std_msgs.msg import String
from std_msgs.msg import Float64
from std_msgs.msg import Bool

MIN = 4095
MAX = 7905
CENTER = 6000

def get_pid_control(ctrl_msg, steering):

    pos_cmd = int(ctrl_msg.data)
    pos_cmd += CENTER
    rospy.loginfo("Position Command: %d", pos_cmd)

    # send position command to sterring servo
    # (don't think this if-else structure should be necessary because of
    # upper_limit and lower_limit params set in launch file)
    if pos_cmd > MAX:
        steering.set_target(MAX)
    elif pos_cmd < MIN:
        steering.set_target(MIN)
    else:
        steering.set_target(pos_cmd)

    # not sure if there should be a sleep command here...
    time.sleep(.05)

def pid_broadcaster():

    with Controller(0) as steering, Controller(1) as motor, \
         Controller(2) as ir_bottom:

        # Publisher init
        setpoint_pub = rospy.Publisher("robot/pid/steering/setpoint", Float64, queue_size=10)
        state_pub = rospy.Publisher("robot/pid/steering/state", Float64, queue_size=10)
        enable_pub = rospy.Publisher("robot/pid/steering/enable", Bool, queue_size=10)

        # Subscriber init
        controlEffort_sub = rospy.Subscriber("robot/pid/steering/control_effort", Float64, get_pid_control, steering)

        # Node init
        rospy.init_node('pid_broadcaster', anonymous=True)

        # enable PID controller
        pid_enable_msg = Bool()
        pid_enable_msg.data = True
        enable_pub.publish(pid_enable_msg)

        # set zero intial velocity
        motor.set_target(CENTER)
        steering.set_target(CENTER)
        time.sleep(2)

        # define setpoint and state messages
        setpoint_msg = Float64()
        state_msg = Float64()

        # define setpoint by averaging initial position data
        distance = []
        for i in range(1,50):
            distance.append(ir_bottom.get_position())
            time.sleep(.01)

        # average of initial IR sensor data
        setpoint = int(sum(distance) / float(len(distance)))
        setpoint_msg.data = setpoint
        setpoint_pub.publish(setpoint_msg)
        print "Setpoint = ",setpoint," cm"

        # set forward speed
        offset = 150
        motor.set_target(CENTER + offset)

        while not rospy.is_shutdown():

            # get position reading from IR sesnor(s)
            position = ir_bottom.get_position()
            rospy.loginfo("IR Position: %f", position)

            # use heading data to correct position measurement

            state_msg.data = position
            state_pub.publish(state_msg)

            # what is this doing?
            time.sleep(0.05)


if __name__ == '__main__':
    try:

        pid_broadcaster()

    except rospy.ROSInterruptException:
        pass