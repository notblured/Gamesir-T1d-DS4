    import asyncio
    from typing import Optional
    import vgamepad as vg
    from bleak import BleakClient
    from enum import IntFlag

    # Define DS4_BUTTONS class to map to DS4 button constants
    class DS4_BUTTONS(IntFlag):
        """
        DualShock 4 digital buttons
        """
        DS4_BUTTON_THUMB_RIGHT = 1 << 15
        DS4_BUTTON_THUMB_LEFT = 1 << 14
        DS4_BUTTON_OPTIONS = 1 << 13
        DS4_BUTTON_SHARE = 1 << 12
        DS4_BUTTON_TRIGGER_RIGHT = 1 << 11
        DS4_BUTTON_TRIGGER_LEFT = 1 << 10
        DS4_BUTTON_SHOULDER_RIGHT = 1 << 9
        DS4_BUTTON_SHOULDER_LEFT = 1 << 8
        DS4_BUTTON_TRIANGLE = 1 << 7
        DS4_BUTTON_CIRCLE = 1 << 6
        DS4_BUTTON_CROSS = 1 << 5
        DS4_BUTTON_SQUARE = 1 << 4

    # Constants for the controller's MAC address and other settings
    CONTROLLER_NAME = "Gamesir-T1d"
    CONTROLLER_MAC = "C6:86:A1:04:BE:00"  # The specified MAC address

    STICK_MIN = -512
    STICK_MAX = 512

    class DS4:
        _previous_state = ""

        def __init__(self):
            self.L1 = 0  # 0 / 1
            self.L2 = 0  # 0 - 255
            self.R1 = 0  # 0 / 1
            self.R2 = 0  # 0 - 255

            self.Triangle = 0  # 0 / 1
            self.Circle = 0  # 0 / 1
            self.Cross = 0  # 0 / 1
            self.Square = 0  # 0 / 1

            self.Share = 0  # 0 / 1
            self.Options = 0  # 0 / 1

            self.LX = 0  # -512 to +512
            self.LY = 0  # -512 to +512
            self.RX = 0  # -512 to +512
            self.RY = 0  # -512 to +512

            self._controller = None
            self.gamepad = vg.VDS4Gamepad()  # Initialize the virtual gamepad

        async def connect(self, address: Optional[str] = None):
            if address is None:
                address = CONTROLLER_MAC  # Use the predefined MAC address
            self._controller = BleakClient(address)
            print("Connecting...")
            await self._controller.connect()
            await self.get_state()
            print("Connected")

        async def get_state(self) -> bool:
            # Returns True if state did change
            self._state_vec = await self._read()
            if self._state_vec[0] == 0xc9:  # Creates garbage values
                return False
            if self._previous_state != self._state_vec:
                self._previous_state = self._state_vec
                self.parse_state()
                return True
            return False

        async def _read(self) -> bytearray:
            return await self._controller.read_gatt_char("00008651-0000-1000-8000-00805f9b34fb")

        def parse_state(self):
            # Notes: Last byte (data[19] is updated on every controller change - can be used as trigger instead of polling)
            data = self._state_vec

            # Button states
            self.L1 = int(bool(data[9] & 0x40))  # Now use LeftThumb input for L1
            self.L2 = int(data[7])  # int 0-255
            self.R1 = int(bool(data[9] & 0x80))
            self.R2 = int(data[8])

            # Correct DS4 Button Mappings
            self.Cross = int(bool(data[9] & 0x01))
            self.Circle = int(bool(data[9] & 0x02))
            self.Square = int(bool(data[9] & 0x08))  # Correct mapping for Square button
            self.Triangle = int(bool(data[9] & 0x10))
            self.Share = int(bool(data[10] & 0x04))
            self.Options = int(bool(data[10] & 0x08))

            # Removed LeftThumb and RightThumb, since they are no longer needed

            # Joystick values (normalize them to -512 to +512 range)
            self.LX = int(((data[2]) << 2) | (data[3] >> 6)) 
            self.LY = int(((data[3] & 0x3f) << 4) + (data[4] >> 4)) 
            self.RX = int(((data[4] & 0xf) << 6) | (data[5] >> 2)) 
            self.RY = int(((data[5] & 0x3) << 8) + ((data[6]))) 

        def simulate_input(self):
            # Simulate button presses using the methods that are available in vgamepad 0.1.0 and DS4_BUTTONS constants
            if self.Cross:
                self.gamepad.press_button(DS4_BUTTONS.DS4_BUTTON_CROSS)  # Using DS4_BUTTONS.CROSS constant
            if self.Circle:
                self.gamepad.press_button(DS4_BUTTONS.DS4_BUTTON_CIRCLE)  # Using DS4_BUTTONS.CIRCLE constant
            if self.Square:
                self.gamepad.press_button(DS4_BUTTONS.DS4_BUTTON_SQUARE)  # Correctly using DS4_BUTTONS.SQUARE constant
            if self.Triangle:
                self.gamepad.press_button(DS4_BUTTONS.DS4_BUTTON_TRIANGLE)  # Using DS4_BUTTONS.TRIANGLE constant

            if self.Share:
                self.gamepad.press_button(DS4_BUTTONS.DS4_BUTTON_SHARE)
            if self.Options:
                self.gamepad.press_button(DS4_BUTTONS.DS4_BUTTON_OPTIONS)

            # Simulate the analog stick positions by directly setting the values
            self.gamepad.left_joystick_float(self.LX / 512, self.LY / 512)  # Normalize to range [-1, 1]
            self.gamepad.right_joystick_float(self.RX / 512, self.RY / 512)  # Normalize to range [-1, 1]

            # Send the simulated input to the virtual gamepad
            self.gamepad.update()

        def __str__(self):
            return "L1: {}\nL2: {}\nR1: {}\nR2: {}\nCross: {}\nCircle: {}\nSquare: {}\nTriangle: {}\nShare: {}\n" \
                "Options: {}\nLX: {}\nLY: {}\nRX: {}\nRY: {}".format(
                self.L1, self.L2, self.R1, self.R2, self.Cross, self.Circle, self.Square, self.Triangle, self.Share,
                self.Options, self.LX, self.LY, self.RX, self.RY
            )


    if __name__ == "__main__":
        async def main():
            controller = DS4()  # Create the controller instance
            await controller.connect()  # Connect using the pre-configured MAC address
            while True:
                if await controller.get_state():
                    controller.simulate_input()  # Simulate the input on virtual gamepad
                    print(controller)

        asyncio.run(main())
