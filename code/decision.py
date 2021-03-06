import numpy as np

# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function

countRobotIsStuck = 0
previousXPos = 0
stuckAtYaw = 0

def checkIfStuck(Rover):
    # This function is to check whether it gets stuck. Especially when it bumps into a rock or at the side of the terrain
    global countRobotIsStuck
    global previousXPos
    global stuckAtYaw
    # This function always check if the rover gets stuck, if it does, it would always need to get out first by doing a turn
    xpos = Rover.pos[0]
    ypos = Rover.pos[1]
    
    if Rover.vel < 0.05 and (abs(previousXPos - xpos) < 2) and not Rover.picking_up:
        countRobotIsStuck += 1
    elif (Rover.vel >= 2) & (abs(Rover.steer) == 15):
        # It is going a roundabout
        countRobotIsStuck += 1
    else:
        countRobotIsStuck = 0
    
    previousXPos = xpos
    
    if countRobotIsStuck > 40:
        Rover.mode = 'stuck'
        countRobotIsStuck = 0
        stuckAtYaw = Rover.yaw
        
    return Rover

def decision_step(Rover):
    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!
    
    # Example:
    # Check if we have vision data to make decisions with
    findRockCount = 0
    
    if Rover.nav_angles is not None:
        
        # Check for Rover.mode status
        if Rover.mode == 'forward': 
            if len(Rover.nav_angles_rock) >= Rover.go_rock:
                # Within navigable range too
                if (np.mean(Rover.nav_angles_rock) > min(Rover.nav_angles)) & (np.mean(Rover.nav_angles_rock) < max(Rover.nav_angles)):
                    print('change to slow mode')
                    findRockCount = 0
                    Rover.mode = 'slow'
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    Rover.steer = np.clip(np.mean(Rover.nav_angles_rock * 180/np.pi), -15, 15)
                
            # Check the extent of navigable terrain
            if len(Rover.nav_angles) >= Rover.stop_forward:  
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle 
                if Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                
                # TODO: is it possible to refine this
                # If there is a wide range of angle, always favour going left
                nav_angles_deg = (Rover.nav_angles * 180/np.pi)
                steering_deg = np.mean(nav_angles_deg)
                Rover.steer = np.clip(steering_deg, -15, 15)
    
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif (len(Rover.nav_angles) < Rover.stop_forward) or (max(Rover.nav_dists) < 50):
                # Set mode to "stop" and hit the brakes!
                Rover.throttle = 0
                # Set brake to stored brake value
                Rover.brake = Rover.brake_set/2
                Rover.steer = 0
                Rover.mode = 'stop'
                
            # Check if the gets stuck    
            Rover = checkIfStuck(Rover)

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    Rover.steer = -15 # Could be more clever here about which way to turn
                
                # If we're stopped but see sufficient navigable terrain in front then go!
                if (len(Rover.nav_angles) >= Rover.go_forward):
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
                
                    
        elif Rover.mode == 'stuck':
            print('stuck')
            
            if (abs(stuckAtYaw - Rover.yaw) > 14):
                Rover.mode = 'forward'
            
            Rover.throttle = 0
            Rover.brake = 0
            Rover.steer = -30
                     
            if (len(Rover.nav_angles) > 10) & (abs(np.mean(Rover.nav_angles * 180/np.pi)) > 30):
                Rover.steer = abs(np.mean(Rover.nav_angles * 180/np.pi)) * -1
            
        
        # If we're already in "slow" mode then it means there is a rock nearby and should inch closer, changing the target to the rock
        elif Rover.mode == 'slow':
            if len(Rover.nav_angles_rock) >= 1: 
                
                Rover.throttle = Rover.throttle_set
                Rover.steer = np.clip(np.mean(Rover.nav_angles_rock * 180/np.pi), -15, 15)
                
                if Rover.vel > (Rover.max_vel/2):
                    Rover.throttle = 0
                    
            else:
                
                if (findRockCount > 10):
                # Sometimes the rock is missed, rather let it go forward then an infinite loop trying to find the rock, try for 10 times
                    Rover.mode = 'forward'
                    Rover.throttle = Rover.throttle_set
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    findRockCount = 0
                    
                findRockCount+=1
                    
                    
            # Always check if stuck
            Rover = checkIfStuck(Rover)
                    
    # Just to make the rover do something 
    # even if no modifications have been made to the code
    else:
        Rover.throttle = Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0
        
        
    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        print('Pick up rock')
        Rover.send_pickup = True
    
    elif Rover.near_sample and not Rover.picking_up:
        print('Set vel to 0 as near sample')
        Rover.vel = 0 
        Rover.throttle = 0
        Rover.brake = 10
    
    # Set it back slow mode to forward
    elif Rover.picking_up:
        Rover.mode = 'forward'
    
    
    return Rover

