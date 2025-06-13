class CharacterModState(beeg_info_menu_state.BeegInfoMenuState):
    name = 'character_mod'

    def start(self):
        super().start()
        self.slot_menu = None
        self.current_slot = None
    
    def draw(self, surf):
        surf = super().draw(surf)
        # Draw the parts of the state that are modifiable

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.handle_mouse()
        if self.info_flag:
            if event == 'INFO' or event == 'BACK':
                get_sound_thread().play_sfx('Info Out')
                self.info_graph.set_transition_out()
                self.info_flag = False
                return

            elif event == 'SELECT':
                box = self.info_graph


            if 'RIGHT' in directions:
                if self.info_graph.move_right():
                    get_sound_thread().play_sfx('Select 6')
            elif 'LEFT' in directions:
                if self.info_graph.move_left():
                    get_sound_thread().play_sfx('Select 6')
            elif 'UP' in directions:
                if self.info_graph.move_up():
                    get_sound_thread().play_sfx('Select 6')
            elif 'DOWN' in directions:
                if self.info_graph.move_down():
                    get_sound_thread().play_sfx('Select 6')

        elif not self.transition:  # Only takes input when not transitioning
            if event == 'INFO':
                get_sound_thread().play_sfx('Info In')
                self.info_graph.set_transition_in()
                self.info_flag = True
                return
            elif event == 'SELECT':
                mouse_position = get_input_manager().get_mouse_position()
                if mouse_position:
                    mouse_x, mouse_y = mouse_position
                    if mouse_x <= 16:
                        self.move_left()
                    elif mouse_x >= WINWIDTH - 16:
                        self.move_right()
                    elif mouse_y <= 16:
                        self.move_up()
                    elif mouse_y >= WINHEIGHT - 16:
                        self.move_down()

            if 'RIGHT' in directions:
                self.move_right()
            elif 'LEFT' in directions:
                self.move_left()
            elif 'DOWN' in directions:
                self.move_down()
            elif 'UP' in directions:
                self.move_up()