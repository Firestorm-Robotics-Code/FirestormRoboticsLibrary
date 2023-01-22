/* By Luke White and Tyler Clarke
    Custom swerve module library using PIDController.
*/
// Note: This and PIDController.hpp need some more cleanup work.

#pragma once

#include <FRL/motor/BaseMotor.hpp>
#include <ctre/Phoenix.h>
#include <iostream>
#include <FRL/motor/PIDController.hpp>

/**
 @author Luke White and Tyler Clarke
 @version 1.0
 
 * Swerve module for FRC. Manages 2 BaseMotor pointers (which because of the polymorphism can be any motor type in FRC)
 */
class SwerveModule {
    /**
     * Motor that controls the rotation of the wheel
     */
    BaseMotor* speed;
    /**
     * Motor that controls the direction of the wheel
     */
    BaseMotor* direction;
    /**
     * PIDController that manages the direction motor
     */
    PIDController* directionController;
    /**
     * CANCoder to use for PID; heap allocated by an ID provided on construction.
     */
    CANCoder* cancoder;

    /**
     * Current percentage that will be applied to the wheel
     */
    double curPercent; // So multiple commands can alter speed
       
    /**
     * SwerveModules are a linked list! This means you can have any number of 'em configured with separate offsets and command them all at once with a single call.
     */
    SwerveModule* linkSwerve;

    /**
     * Whether or not the SwerveModule is linked to another one.
     */
    bool isLinked = false;  

    /**
     * Configured offset.
     */
    double encoderOffset;

    short swerveRole;
    
public:
    /**
     * Constructor
     @param speedMotor The motor to use for wheel speed control
     @param directionMotor The motor to use for wheel direction control
     @param CanCoderID The CAN id of the CANCoder
     @param offset The offset of the wheel, in encoder ticks
     @param speedInverted Whether or not to invert the wheel speed motor
     @param direcInverted Whether or not to invert the wheel direction motor
     */
    SwerveModule(BaseMotor* speedMotor, BaseMotor* directionMotor, int CanCoderID, short role, double offset, bool speedInverted=false, bool direcInverted=false) {
        encoderOffset = offset;
        speed = speedMotor;
        direction = directionMotor;
        cancoder = new CANCoder {CanCoderID};
        
        swerveRole = role;
        directionController = new PIDController (direction);
        directionController -> constants.P = 0.0005;
        //directionController -> constants.I = 0.0001;
        directionController -> constants.MaxOutput = 0.2;
        directionController -> constants.MinOutput = -0.2;
        directionController -> SetCircumference(4096);
        
        speed -> SetInverted(speedInverted);
        direction -> SetInverted(direcInverted);
    }
    
    /**
     * Link to another swerve module
     @param LinkSwerve The swerve module to link to
     */
    void Link(SwerveModule* LinkSwerve) {
        isLinked = true;           
        linkSwerve = LinkSwerve; 
    }
    
    bool withinDeadband(double num, double deadband, double reference = 0) {
        return num - deadband >= reference - deadband && num + deadband <= reference + deadband;
    }
    
    /**
     * Get the current (physical) direction of the module
     */
    
    long GetDirection() {
        return smartLoop(cancoder -> GetAbsolutePosition() - encoderOffset);
    }
    /**
     * Returns true if at a position (with a deadband)
     */
    
    bool isAtPosition(double position) {
        if (withinDeadband(GetDirection(), 5, position)) {
            return true;
        }
        return false;
    }
    
    double coterminal(double angle) {
        while (angle >= 360) {
            angle -= 360;
        }
        while (angle < 0) {
            angle += 360;
        }
        return angle;
    }
    
    /**
     * Set the direction of the motor.
     @param targetPos The encoder tick to aim for
     */
    
    void SetDirection(double targetPos, bool followLink = true) {
        directionController -> SetPosition(targetPos);
        directionController -> Update(GetDirection());
        if (isLinked && followLink){
            linkSwerve -> SetDirection(targetPos);
        }
    }

    /**
     Increase the speed of the wheel motor
     @param spd Percentage to add
     @param followLink Whether or not to command the linked swerve module, if it exists
     */
    void MovePercent(double spd, bool followLink = true){
        curPercent += spd;
        if (isLinked && followLink){
            linkSwerve -> MovePercent(spd);
        }
    }

    /**
     Apply a percentage to the wheel motor
     */
    void ApplySpeed(){
        speed -> SetPercent(curPercent);
        curPercent = 0; // Velocity ain't "sticky", this is a safety thing
        if (isLinked){
            linkSwerve -> ApplySpeed();
        }
    } 
    
    /**
     * Orient the swerve drive 
     */
    
    void Orient(int angle, int currentAngle) {
        if (angle != -1) {
            if (swerveRole == 1 || swerveRole == 3) {
                SetDirection((4096/360) * 45, false);
            }
            else {
                SetDirection((4096/360) * 315, false);
            }
        }
    }
};
