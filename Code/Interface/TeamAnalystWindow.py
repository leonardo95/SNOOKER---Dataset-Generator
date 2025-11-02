# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 15:01:46 2021

@author: Leonardo Ferreira
@goal: Interface for the personalization of the analysts and incidents 
"""

from Code.Configurator import Configurator 
from Code.InterfaceUtils import InterfaceUtils 

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QLabel,
    QScrollArea,
    QRadioButton,
    QLineEdit,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QWidget
)

# TeamAnalystWindow class
class TeamAnalystWindow(QScrollArea):
    def __init__(self, *args, **kwargs):
        """
        TeamAnalystWindow constructor.

        Parameters
        ----------
        *args : str
            Parameters related to window identification (domain and window type).
        **kwargs : str
            domain - cybersecurity; window type - Analysts.

        Returns
        -------
        None.

        """
        super().__init__()
        self.args = args
        self.kwargs = kwargs
        self.parent_windows = self.args[0]
        self.type = self.args[1]
        
        self.setWindowIcon(QtGui.QIcon('./Resources/Icons/tkinter_icon.ico'))
        InterfaceUtils.set_widgets_style(self, "Styles\style.css")
        InterfaceUtils.set_fonts(self)
            
        self.standard_teams, self.custom_teams, self.analysts = {}, {}, {}
        self.setup_teams_UI()   
        
    def setup_teams_UI(self):
        """
        Setups TeamAnalystWindow's UI.

        Returns
        -------
        None.

        """
        self.centralWidget = QWidget()
        main_layout = QVBoxLayout(self.centralWidget)
        
        self.setWindowTitle("Teams and Analysts Configurator")
        self.setWindowIcon(QtGui.QIcon('./Resources/Icons/SNOOKER.png'))

        generation_layout = QHBoxLayout()
            
        self.team_modes = InterfaceUtils.create_groupbox(self, "Team Generation Mode:", generation_layout, self.features_font, True)  
        self.team_standard = InterfaceUtils.create_radiobox("Standard", True)
        self.team_standard.toggled.connect(lambda:self.pick_team_mode(self.team_standard, main_layout))
        self.team_custom = QRadioButton("Custom")
        self.team_custom.toggled.connect(lambda:self.pick_team_mode(self.team_custom, main_layout))
            
        # Shift QCheckBox
        self.shifts = InterfaceUtils.create_checkbox("Balanced", None, self.parent_windows.generation_params["balanced_shifts"])
        self.shifts.setHidden(True)
        self.shifts.stateChanged.connect(self.pick_shift_method)
        
        generation_layout.addWidget(self.team_standard, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        generation_layout.addWidget(self.team_custom, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
        generation_layout.addWidget(self.shifts, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        main_layout.addWidget(self.team_modes)
        
        for curr_team in self.parent_windows.generation_params["analysts_skills"].keys():
            self.custom_teams[curr_team] = {}
        
        self.initiate_teams(main_layout)
        self.set_analysts_data(main_layout)        

        self.setWidget(self.centralWidget)
        self.setWidgetResizable(True)
        
################################ FUNCTIONS ###############################

    def load_teams_data(self):
        """
        Loads the team configurations from external file.

        Returns
        -------
        None.

        """
        filename = Configurator.load_configuration_data(self, './Configurations/{self.domain}/Init_cfg.yaml')

        if filename:
            while len(self.analysts) != 0:
                analyst_name = list(self.analysts.keys())[0]
                team = self.get_team_analyst(self.custom_teams, analyst_name)
                self.remove_analyst(team, analyst_name) 
                
            config_data = Configurator.read_configuration_file(self.domain, filename)
            
            if Configurator.check_param_in_config(config_data, "teams_info_pool") and Configurator.check_param_in_config(config_data, "analysts_info"):
                temp_teams = config_data["teams_info_pool"]
                temp_analysts = config_data["analysts_info"]

                for analyst in temp_analysts.keys():
                    for team in temp_teams.keys():
                        if analyst in list(temp_teams[team]):
                            shift = temp_analysts[analyst]["shift"]
                            growth = round(temp_analysts[analyst]["growth"], 2)  
                            refusal_rate = round(temp_analysts[analyst]["refusal_rate"], 2)
                            self.add_analyst_data(analyst, team, shift, growth, refusal_rate)
            
                self.parent_windows.generation_params["analysts_skills"] = temp_analysts 
                #print(temp_analysts)
                print("Teams loaded successfully!")
            else:
                print("Impossible to load configuration!")
            self.close()

    def add_analyst_data(self, name, team, shift, growth, acceptance_rate):    
        """
        Adds a new operator to a team.

        Parameters
        ----------
        name : str
            Operator name.
        team : str
            Team name.
        shift : int
            Work shift.
        growth : float
            Operator growth rate.
        acceptance_rate : float
            Operator acceptance rate.

        Returns
        -------
        None.

        """        
        if not name:    
            InterfaceUtils.pop_message("Analyst Building", "The name cannot be empty!")
        elif name not in self.analysts.keys():
            self.analysts[name] = {}
            self.custom_teams[team]['analysts'].append(name)
            self.analysts[name]['team'] = team
        
            analyst_layout = QHBoxLayout()
    
            self.custom_teams[team]['no analysts widget'].setHidden(True)
            self.analyst_label = QLabel("Analyst:" , self) 
            self.analyst_label.setFont(self.features_font)
            self.analysts[name]['widget label name'] = self.analyst_label
            self.analyst = QLabel(name , self) 
            self.analysts[name]['widget name'] = self.analyst
            
            self.shift_label = QLabel("Shift:" , self) 
            self.shift_label.setFont(self.features_font)
            self.analysts[name]['widget label shift'] = self.shift_label
            self.shift = QLabel(str(self.curr_analyst_shift.itemText(shift)) , self) 
            self.analysts[name]['widget shift'] = self.shift
            self.analysts[name]['widget shift index'] = shift
            
            self.growth_label = QLabel("Growth:" , self) 
            self.growth_label.setFont(self.features_font)
            self.analysts[name]['widget label growth'] = self.growth_label
            self.growth = QLabel(str(growth) , self) 
            self.analysts[name]['widget growth'] = self.growth
            
            self.acceptance_label = QLabel("Acceptance rate:" , self) 
            self.acceptance_label.setFont(self.features_font)
            self.analysts[name]['widget label acceptance'] = self.acceptance_label
            self.acceptance = QLabel(str(acceptance_rate) , self) 
            self.analysts[name]['widget acceptance'] = self.acceptance

            self.remove_analyst_button = InterfaceUtils.create_button(self, "", "removeAnalyst", None)     
            self.remove_analyst_button.setFixedSize(48, 48)

            self.remove_analyst_button.setIcon(QtGui.QIcon('Resources/Icons/remove.ico'))
            self.remove_analyst_button.setIconSize(QSize(48, 48))
            self.analysts[name]['widget delete'] = self.remove_analyst_button
            self.remove_analyst_button.clicked.connect(lambda:self.remove_analyst(team, name))
            
            analyst_layout.addWidget(self.analyst_label, alignment = Qt.AlignLeft | Qt.AlignVCenter)
            analyst_layout.addWidget(self.analyst, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
            analyst_layout.addWidget(self.shift_label, alignment = Qt.AlignRight | Qt.AlignVCenter)
            analyst_layout.addWidget(self.shift, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
            analyst_layout.addWidget(self.growth_label, alignment = Qt.AlignRight | Qt.AlignVCenter)
            analyst_layout.addWidget(self.growth, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
            analyst_layout.addWidget(self.acceptance_label, alignment = Qt.AlignRight | Qt.AlignVCenter)
            analyst_layout.addWidget(self.acceptance, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
            analyst_layout.addWidget(self.remove_analyst_button, alignment = Qt.AlignRight | Qt.AlignVCenter)
            layout = self.custom_teams[team]['layout']
            layout.addLayout(analyst_layout)
                
            self.curr_analyst_name.setText("")
        else:
            InterfaceUtils.pop_message(self, "Analyst Building", "There is already an analyst with the same name!")
                 
    def remove_analyst(self, team, analyst_name):
        """
        Removes an operator from a team.

        Parameters
        ----------
        team : str
            Team analyzed.
        analyst_name : str
            Analyst name to remove.

        Returns
        -------
        None.

        """
        print(f'delete {analyst_name} from {team}')
        self.custom_teams[team]['analysts'].remove(analyst_name)
        self.analysts[analyst_name]['widget label name'].setParent(None)
        self.analysts[analyst_name]['widget name'].setParent(None)
        self.analysts[analyst_name]['widget label shift'].setParent(None)
        self.analysts[analyst_name]['widget shift'].setParent(None)
        self.analysts[analyst_name]['widget label growth'].setParent(None)
        self.analysts[analyst_name]['widget growth'].setParent(None)
        self.analysts[analyst_name]['widget label acceptance'].setParent(None)
        self.analysts[analyst_name]['widget acceptance'].setParent(None)
        self.analysts[analyst_name]['widget delete'].setParent(None)
        del(self.analysts[analyst_name])
        
        if not self.custom_teams[team]['analysts']:
            self.custom_teams[team]['no analysts widget'].setHidden(False)
        
    def set_analysts_data(self, main_layout):
        """
        Sets the panel for newly added operators in the main layout.

        Parameters
        ----------
        main_layout : QVBoxLayout
            Layout of the newly added operators.

        Returns
        -------
        None.

        """
        analyst_input_layout = QVBoxLayout()
        
        self.analysts_input = InterfaceUtils.create_groupbox(self, "Analyst Input", analyst_input_layout, self.features_font, True)  
        self.analysts_input.setHidden(True)
        main_layout.addWidget(self.analysts_input)
        
        curr_analyst_layout = QHBoxLayout()
        
        self.curr_analyst_name_label = QLabel("Name:", self)
        self.curr_analyst_name = QLineEdit()
        curr_analyst_conf_layout = QHBoxLayout()
        self.curr_analyst_team_label = QLabel("Team:", self)
        self.curr_analyst_team = QComboBox()
        self.curr_analyst_team.addItems(list(self.parent_windows.generation_params["analysts_skills"].keys()))
        self.curr_analyst_shift_label = QLabel("Shift:", self)
        self.curr_analyst_shift = QComboBox()
        self.curr_analyst_shift.addItems(["00:00-08:00", "08:00-16:00", "16:00-24:00"])
        self.curr_analyst_growth_label = QLabel("Growth:", self)
        self.curr_analyst_growth = InterfaceUtils.create_doublespin(self, 1, 2, 0.01, 1)
        self.curr_analyst_acceptance_label = QLabel("Acceptance rate:", self)
        self.curr_analyst_acceptance = InterfaceUtils.create_doublespin(self, 0.01, 0.2, 0.01, 1)
        self.add_analyst_button = InterfaceUtils.create_button(self, "", "addAnalyst", None)
        self.add_analyst_button.setFixedSize(42, 42)
        self.add_analyst_button.setIcon(QtGui.QIcon('Resources/Icons/add.ico'))
        self.add_analyst_button.setIconSize(QSize(42, 42))
        self.add_analyst_button.setHidden(True)  
        
        curr_analyst_layout.addWidget(self.curr_analyst_name_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        curr_analyst_layout.addWidget(self.curr_analyst_name)
        curr_analyst_layout.addWidget(self.curr_analyst_team_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        curr_analyst_layout.addWidget(self.curr_analyst_team)
        curr_analyst_layout.addWidget(self.curr_analyst_shift_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        curr_analyst_layout.addWidget(self.curr_analyst_shift)
        
        curr_analyst_conf_layout.addWidget(self.curr_analyst_growth_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        curr_analyst_conf_layout.addWidget(self.curr_analyst_growth, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        curr_analyst_conf_layout.addWidget(self.curr_analyst_acceptance_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        curr_analyst_conf_layout.addWidget(self.curr_analyst_acceptance, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        curr_analyst_conf_layout.addWidget(self.add_analyst_button, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        
        analyst_input_layout.addLayout(curr_analyst_layout)
        analyst_input_layout.addLayout(curr_analyst_conf_layout)
               
        main_layout.addLayout(analyst_input_layout)
        self.add_analyst_button.clicked.connect(lambda:self.add_analyst_data(self.curr_analyst_name.text(), self.curr_analyst_team.currentText(), self.curr_analyst_shift.currentIndex(), self.curr_analyst_growth.value(), self.curr_analyst_acceptance.value()))
        
        for curr_team in self.parent_windows.generation_params["analysts_skills"].keys():
            self.custom_teams[curr_team]['analysts'] = []   
            self.no_analysts = QLabel("No analysts created!", self) 
            self.custom_teams[curr_team]['no analysts widget'] =  self.no_analysts 
            
            layout = QVBoxLayout()
            self.custom_teams[curr_team]['layout'] = layout
            
            self.team = InterfaceUtils.create_groupbox(self, f'Team {curr_team}', layout, self.features_font, True)
            self.team.setHidden(True)
            self.custom_teams[curr_team]['groupbox widget'] = self.team
            
            layout.addWidget(self.no_analysts) 
            main_layout.addWidget(self.team, alignment=Qt.AlignTop)
            
        self.analyst_information = QLabel("Note: All teams should have at least three analysts!", self)
        self.analyst_information.setHidden(True)
        main_layout.addWidget(self.analyst_information, alignment=Qt.AlignTop)
        
        self.save_team_config_button = InterfaceUtils.create_button(self, "", "saveConfig", None)
        self.save_team_config_button.setFixedSize(48, 48)
        self.save_team_config_button.setIcon(QtGui.QIcon('Resources/Icons/save.ico'))
        self.save_team_config_button.setIconSize(QSize(64, 64))
        self.save_team_config_button.setHidden(True)  
        self.save_team_config_button.clicked.connect(self.save_team_data)
           
        self.load_teams_button = InterfaceUtils.create_button(self, "", "loadConfig", None)
        self.load_teams_button.setFixedSize(48, 48)
        self.load_teams_button.setIcon(QtGui.QIcon('Resources/Icons/load.ico'))
        self.load_teams_button.setIconSize(QSize(64, 64))
        self.load_teams_button.setHidden(True)  
        self.load_teams_button.clicked.connect(self.load_teams_data)
        
        custom_buttons_layout = QHBoxLayout()
        custom_buttons_layout.addWidget(self.save_team_config_button, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        custom_buttons_layout.addWidget(self.load_teams_button, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        main_layout.addLayout(custom_buttons_layout)
    
    def save_team_data(self):
        """
        Saves team configurations on a external file.

        Returns
        -------
        None.

        """
        message = ""
        for team in self.custom_teams.keys():
            shifts_available = list(self.parent_windows.treatment_params["shifts"].keys())
            
            if len(self.custom_teams[team]['analysts']) < 1:
                message = f'{message}Team {team}'
                if team is list(self.custom_teams.keys())[-1]:
                    message = f'{message} have no analysts!'
                else:
                    message = f'{message}, '
        
        if message == "":
            InterfaceUtils.pop_message("Team Building", message)
        else:
            filename = Configurator.save_dialog(self)
            if filename == "":
               #InterfaceUtils.pop_message("Team Building", message)
               print("Team new configuration canceled!")
            else: 
                temp_teams, temp_analysts = {}, {}
            
                for new_team in self.custom_teams.keys():
                    temp_teams[new_team] = []
                    temp_teams[new_team] = self.custom_teams[new_team]['analysts']
                
                    for new_analyst in temp_teams[new_team]:
                        temp_analysts[new_team] = {}
                        temp_analysts[new_team]["analysts"] = {}
                        temp_analysts[new_team]["analysts"][new_analyst] = {}
                        shift_index = int(self.analysts[new_analyst]["widget shift index"])
                        temp_analysts[new_team]["analysts"][new_analyst]['shift'] = shift_index
                        temp_analysts[new_team]["analysts"][new_analyst]["growth"] = float(self.analysts[new_analyst]["widget growth"].text())
                        temp_analysts[new_team]["analysts"][new_analyst]["refusal_rate"] = float(self.analysts[new_analyst]["widget acceptance"].text())
                        

                Configurator.save_new_config_file(self.domain, "analysts_info", temp_analysts, filename)
                self.parent_windows.generation_params["analysts_skills"] = temp_analysts
                print("Analysts assigned successfully!")
            self.close()
            
    def get_team_analyst(self, teams, name):
        """
        Gets the team of an analyst.

        Parameters
        ----------
        teams : dict
            Comprises information about the teams and their operators.
        name : str
            Operator name.

        Returns
        -------
        team : str
            Team of the operator inspected.

        """
        for team in teams.keys():
            if name in teams[team]['analysts']:
                return team   
           
    def pick_shift_method(self):
        """
        Enables all work shifts occupied.

        Returns
        -------
        None.

        """
        if self.shifts.isChecked():
            print("All shifts will have analysts")
            self.parent_windows.generation_params["balanced_shifts"] = True
            self.analyst_information.setText("Note: All teams should have at least three analysts!")
        else:
            print("There may be shifts with no analysts")
            self.parent_windows.generation_params["balanced_shifts"] = False
            self.analyst_information.setText("Note: All teams should have at least one analyst!")
            
    def initiate_teams(self, main_layout):
        """
        Setups the initial teams known by the system.

        Parameters
        ----------
        main_layout : QVBoxLayout
            Layout where initial teams are shown.

        Returns
        -------
        None.

        """
        for team in self.parent_windows.generation_params["analysts_skills"].keys():
            self.standard_teams[team] = {}
            self.standard_teams[team]['analysts'] = list(self.parent_windows.generation_params["analysts_skills"].keys())
            
            team_layout = QHBoxLayout()
            
            self.curr_team = InterfaceUtils.create_groupbox(self, f'Team {team}', team_layout, self.features_font, True)
            self.curr_team_analysts = QLabel(str("Analysts: " + (', '.join(list(self.parent_windows.generation_params["analysts_skills"][team]["analysts"].keys())))), self)
            self.standard_teams[team]['widget'] = self.curr_team
            
            team_layout.addWidget(self.curr_team_analysts)
            main_layout.addWidget(self.curr_team)
        
    def pick_team_mode(self, mode, main_layout):
        """
        Changes between standard and custom teams.

        Parameters
        ----------
        mode : QRadioButton
            Standard or Custom teams.
        main_layout : QVBoxLayout
            Layout where teams are shown.

        Returns
        -------
        None.

        """
        if mode.text() == "Standard" and mode.isChecked():
            for team in self.standard_teams:
                widget = self.standard_teams[team]['widget']
                widget.setHidden(False)
                self.add_analyst_button.setHidden(True)
                self.analysts_input.setHidden(True)
                #self.teams_customizable.setHidden(True)
                    
            for team in self.custom_teams:
                self.custom_teams[team]['groupbox widget'].setHidden(True)
                
            self.shifts.setHidden(True)
            self.analyst_information.setHidden(True)
            self.save_team_config_button.setHidden(True)  
            self.load_teams_button.setHidden(True)  
        if mode.text() == "Custom" and mode.isChecked():
            for team in self.standard_teams:
                widget = self.standard_teams[team]['widget']
                widget.setHidden(True)
                self.add_analyst_button.setHidden(False)
                self.analysts_input.setHidden(False)
                #self.teams_customizable.setHidden(False)
                    
            for team in self.custom_teams:
                self.custom_teams[team]['groupbox widget'].setHidden(False)
                    
            self.shifts.setHidden(False)
            self.analyst_information.setHidden(False)
            self.save_team_config_button.setHidden(False)  
            self.load_teams_button.setHidden(False)  
            
    def closeEvent(self, event):
        """
        Closes all events.

        Parameters
        ----------
        event : event
            Events running.

        Returns
        -------
        None.

        """
        if self.isActiveWindow():
            self.parent_windows.subwindows.remove(self)
        self.close()