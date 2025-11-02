"""
Created on Mon Dec 21 12:16:30 2020

@author: leonardo Ferreira
@goal: Generator Main's Interface
"""
from Code.Configurator import Configurator
from TeamAnalystWindow import TeamAnalystWindow
from SQLConnectionWindow import SQLConnectionWindow
from CheckableComboBox import CheckableComboBox 
from Code.InterfaceUtils import InterfaceUtils 
from Code.Utils import Utils
from Code.Generator.DatasetGenerator import DatasetGenerator

import string, sys, os, psutil
from datetime import datetime
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, QTime, QThreadPool
from PyQt5 import QtGui, QtCore
import ctypes

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QScrollArea,
    QTabWidget,
    QDesktopWidget,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QWidget,
)

# WorkerSignals class for sending signals about the generation
class WorkerSignals(QObject):
    
    finished = pyqtSignal()
    progress = pyqtSignal(int)

# Thread used to generate the dataset while interface is updated
class Generator(QRunnable):
    finished = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        """
        SNOOKER constructor

        Parameters
        ----------
        *args : many types
            Multiple arguments related to the generation.
        **kwargs : many types
            Arguments can have various content.

        Returns
        -------
        None.

        """
        super(Generator, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.canceled = False
        
    def run(self):
        """
        Runs the DatasetGenerator class to build synthetic datasets with the defined configurations.

        Returns
        -------
        None.

        """
        #print("\014")
        Utils.close_excel()
        #Utils.reset_generation_folder("Output/Generation/")
        self.dataset_generator = DatasetGenerator(self, self.args[1]["logger_active"], "./Configurations/")
        self.dataset_generator.build_datasets('Resources/Countries/Countries_updated.json')
        self.signals.finished.emit()
        
# Main Window Interface
class SNOOKER(QMainWindow):
    def __init__(self, cpu_times_before, cpu_usage_before, parent=None):
        """
        SNOOKER main interface constructor

        Parameters
        ----------
        cpu_times_before : scpustimes
            Comprises information about CPU time statistics.
        cpu_usage_before : float
            Percentage of total CPU time.
        parent : QMainWindow, optional
            Parent window. The default is None.

        Returns
        -------
        None.

        """
        super().__init__(parent)
        
        self.setWindowTitle("SNOOKER - Dataset Generator")
        InterfaceUtils.set_widgets_style(self, "Styles/style.css")
        self.setWindowIcon(QtGui.QIcon('./Resources/Icons/SNOOKER.png'))
        
        self.cpu_times_before = cpu_times_before
        self.cpu_usage_before = cpu_usage_before
            
        self.dataset_field_pool = ["Cybersecurity", "Education" "Finance", "Health"]
        
        self.auxiliar_dataset_params = {'country': True, 'country time': False, 'raised_tsp': True, 'allocated_tsp': True, 'stages': True, 'client': True, 
                                   'team analysts': False, 'wait time': True, 'shifted': False, 'subfamily action duration': False, 
                                   'analysts available': False, 'analysts actions':False, 'analysts actions status': False, 
                                   'analyst shift': False, 'prioritized': False, 'escalate': True, 'coordinated': False, 'suspicious': False,
                                   'source ip': True, 'source port': True, 'destination ip': True, 'destination port': True, 'feature': True}
        
        self.interface_params, self.generation_params, self.treatment_params, self.init_suspicious_countries = Configurator.load_configurations("Cybersecurity")
        self.generation_params["suspicious_ips"] = Configurator.get_suspicious_ips()
        self.generation_params["special_steps"] = Configurator.instantiate_special_steps(self.generation_params['max_transfer_steps'])
        
        self.datasets_available = Utils.contains_files("./Resources/Datasets") 
        
        if self.datasets_available:
            self.file = Utils.get_smallest_file("./Resources/Datasets/")
            print("File:", self.file)
            self.generation_params["ticket_seasonality"], self.generation_params["family_seasonality"], self.generation_params["family_mean_duration"], self.generation_params["family_mapping"], self.generation_params["real_family_probs"], self.generation_params["real_dataset"] = Configurator.get_ticket_seasonality(self.file, False, None, False)
        else:
            self.generation_params["ticket_seasonality"], self.generation_params["family_seasonality"], self.generation_params["family_mean_duration"], self.generation_params["family_mapping"], self.generation_params["real_family_probs"], self.generation_params["real_dataset"] = None, None, None, None, None, None
            self.generation_params["ticket_seasonality_selector"], self.generation_params["family_seasonality_selector"], self.generation_params["techniques_seasonality_selector"] = False, False, False
            self.file = "No real data!"
        self.countries_list = Configurator.get_countries_names('Resources/Countries/Countries_updated.json' )
    
        
        InterfaceUtils.set_fonts(self)
        self.subwindows = list()
        self.setup_main_UI()
        self.activateWindow()
    
    def setup_main_UI(self):
        """
        Setups the SNOOKER's UI.

        Returns
        -------
        None.

        """    
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        
        main_window_layout = QVBoxLayout()
        self.centralWidget.setLayout(main_window_layout)
        
        main_tabwidget = QTabWidget()
        main_tabwidget.addTab(self.setup_dataset_generation_tab(),"Dataset Generation")
        main_tabwidget.addTab(self.setup_optional_parameters_tab(),"Options")
        
        main_window_layout.addWidget(main_tabwidget)
     
    def setup_optional_parameters_tab(self):
        """
        Setups the Options Tab.

        Returns
        -------
        QWidget
            Widget with options tab.

        """   
        main_layout = QVBoxLayout()
        self.optionsTab = QWidget()
        
        self.load_selectors_widgets(main_layout)
        self.load_suspicious_countries_widgets(main_layout)
        self.load_outlier_widgets(main_layout)
        self.optionsTab.setLayout(main_layout)
        
        return self.optionsTab
        
    def setup_dataset_generation_tab(self):
        """
        Setups the main tab (configuration of the main generation parameters).

        Returns
        -------
        QWidget
            Generation widget.

        """
        self.generationTab = QWidget()
        main_layout = QVBoxLayout()

        self.tabs = QTabWidget()
        # Ticket
        self.tabs.addTab(self.load_ticket_widgets(self.tabs), "Tickets")
        # Family Generation
        self.tabs.addTab(self.load_family_widgets(), "Family")
        # Techniques
        self.tabs.addTab(self.load_technique_widgets(), "Techniques")
        # Learning
        self.tabs.addTab(self.load_learning_widgets(), "Learning")

        # Generation Modes
        self.load_generation_modes()
        # Team Customization
        self.load_team_widgets()
        # Generate Button
        generate_layout = self.load_generate_button()
        
        # Set the layout
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.generation)
        main_layout.addWidget(self.teams_configs)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(generate_layout)
        
        self.generationTab.setLayout(main_layout)
        
        return self.generationTab 
   
    def load_selectors_widgets(self, main_layout):
        """
        Configures the IP, Track Behaviours and Outliers of the Options Tab

        Parameters
        ----------
        main_layout : QVBoxLayout
            Layout of the options tab.

        Returns
        -------
        None.
        
        """   
        options_params_layout = QHBoxLayout()
        ip_label = QLabel("IP:")
        options_params_layout.addWidget(ip_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.ip_toggle = InterfaceUtils.create_toogle(self.generation_params["ip_selector"])
        options_params_layout.addWidget(self.ip_toggle, alignment=Qt.AlignLeft) 
        self.ip_toggle.stateChanged.connect(self.pick_ip)
        
        track_behaviour_label = QLabel("Track Behaviours:")
        options_params_layout.addWidget(track_behaviour_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.track_behaviour_toggle = InterfaceUtils.create_toogle(False)
        options_params_layout.addWidget(self.track_behaviour_toggle, alignment=Qt.AlignLeft) 
        self.track_behaviour_toggle.stateChanged.connect(self.pick_suspicious_method)
        
        outlier_label = QLabel("Outliers:")
        options_params_layout.addWidget(outlier_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.outlier_toggle = InterfaceUtils.create_toogle(self.interface_params["outlier_selector"])
        options_params_layout.addWidget(self.outlier_toggle, alignment=Qt.AlignLeft) 
        self.outlier_toggle.stateChanged.connect(self.pick_outlier_method)
        
        output_parameters_layout = QHBoxLayout()
        output_parameters_label = QLabel("Output Parameters:")
        output_parameters_layout.addWidget(output_parameters_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
    
        self.output_parameters_combo = CheckableComboBox("aux_params", None)
        
        for i in range(len(self.auxiliar_dataset_params.keys())):
            self.output_parameters_combo.addItem(list(self.auxiliar_dataset_params.keys())[i])
            item = self.output_parameters_combo.model().item(i, 0)
            temp_param = list(self.auxiliar_dataset_params.keys())[i]
            if self.auxiliar_dataset_params[temp_param]:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            
        output_parameters_layout.addWidget(self.output_parameters_combo, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.output_parameters_combo.activated.connect(self.update_output_params)   
        
        ip_layout = QHBoxLayout()  
        self.ip_groupbox = InterfaceUtils.create_groupbox(self, "IP Configurations:", ip_layout, self.features_font, self.generation_params["ip_selector"])
        
        self.ip_type = InterfaceUtils.create_combox(self.generation_params["ips_pool"])
        self.ip_type.currentIndexChanged.connect(self.pick_IP_address)   
        ip_layout.addWidget(self.ip_type, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
        
        options_params_layout.addLayout(output_parameters_layout)
        main_layout.addLayout(options_params_layout)
        main_layout.addWidget(self.ip_groupbox)
    
    def load_suspicious_countries_widgets(self, main_layout):
        """
        The tracked countries are customized (hour, countries and days off) and loaded according the configuration file.    

        Parameters
        ----------
        main_layout : QVBoxLayout
            Layout of the options tab.
        
        Returns
        -------
        None.
        
        """
        self.countries_grid = QGridLayout() 
        scroll = QScrollArea()      
        scroll_content = QWidget()
        self.scroll_content_layout = QVBoxLayout()
        scroll_content.setLayout(self.scroll_content_layout)
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_content)
        
        sus_countries_layout = QVBoxLayout() 
        self.sus_countries_groupbox = InterfaceUtils.create_groupbox(self, "Suspicious Countries Configurations:", sus_countries_layout, self.features_font, self.interface_params["suspicious_selector"])
    
        selectable_countries_layout = QHBoxLayout()
        sus_countries_label = QLabel("Countries:")
        selectable_countries_layout.addWidget(sus_countries_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        
        self.sus_countries_combo = CheckableComboBox("countries", 0)

        for i in range(len(self.countries_list)):
            self.sus_countries_combo.addItem(self.countries_list[i])
            item = self.sus_countries_combo.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)
        selectable_countries_layout.addWidget(self.sus_countries_combo, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
            
        sus_subfamilies_label = QLabel("Subfamilies:")
        selectable_countries_layout.addWidget(sus_subfamilies_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
      
        sus_subfamilies_spin = InterfaceUtils.create_doublespin(self, 0, 1, 0.01, self.generation_params["suspicious_subfamily"])
        sus_subfamilies_spin.valueChanged.connect(self.update_country_subfamily)
        selectable_countries_layout.addWidget(sus_subfamilies_spin, alignment=Qt.AlignLeft | Qt.AlignVCenter) 

        sus_dates_layout = QHBoxLayout()
        sus_dates_widget = QWidget()
        sus_dates_widget.setEnabled(False)
        sus_dates_widget.setLayout(sus_dates_layout)
        
        sus_countries_start_label = QLabel("Start:")
        sus_dates_layout.addWidget(sus_countries_start_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
        
        self.sus_countries_start_time = InterfaceUtils.create_timedit(self, QTime(22, 00, 00), "hourSelector", 'hh:mm:ss:mm:zz')   
        sus_dates_layout.addWidget(self.sus_countries_start_time, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
        
        sus_countries_end_label = QLabel("End:")
        sus_dates_layout.addWidget(sus_countries_end_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
        
        self.sus_countries_end_time = InterfaceUtils.create_timedit(self, QTime(7, 00, 00), "hourSelector", 'hh:mm:ss:mm:zz')
        sus_dates_layout.addWidget(self.sus_countries_end_time, alignment=Qt.AlignHCenter | Qt.AlignVCenter)  
        
        sus_dates_lock_layout = QHBoxLayout()
        sus_dates_lock_layout.addWidget(sus_dates_widget, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        
        self.sus_countries_lock = InterfaceUtils.create_button(self, "", "country_lock", "locked")
        self.sus_countries_lock.clicked.connect(lambda:self.lock_dates(sus_dates_widget))
        self.sus_countries_lock.setFixedSize(40, 40)
        self.sus_countries_lock.setIcon(QtGui.QIcon('Resources/Icons/locked.ico'))
        self.sus_countries_lock.setIconSize(QSize(40, 40))
        sus_dates_lock_layout.addWidget(self.sus_countries_lock, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        if self.interface_params["suspicious_selector"]:
            self.add_suspicious_countries()
        
        self.scroll_content_layout.addLayout(self.countries_grid)
        self.track_behaviour_toggle.setChecked(self.interface_params["suspicious_selector"])
        
        sus_countries_layout.addLayout(selectable_countries_layout)
        sus_countries_layout.addLayout(sus_dates_lock_layout)
        sus_countries_layout.addWidget(scroll)

        self.sus_countries_combo.activated.connect(self.add_single_suspicious_country)    
        main_layout.addWidget(self.sus_countries_groupbox)
    
    def load_generation_modes(self):        
        """
        The generation can be standard (data from configuration file) or customized. The debug option is also presented to help understanding the generation.    

        Returns
        -------
        None.
        
        """
        generation_layout = QVBoxLayout()
        mode_layout = QHBoxLayout()
        
        self.generation = InterfaceUtils.create_groupbox(self, "Generation Mode:", generation_layout, self.features_font, True)
        
        load_files_layout = QHBoxLayout()
                
        self.fileButton = QPushButton(f'{self.file}')
       
        if self.file != "No real data!":
            print("There is real data!")
            self.real_data_box = InterfaceUtils.create_checkbox("Real data", "real_dataset", True)
        else:
            self.real_data_box = InterfaceUtils.create_checkbox("Real data", "real_dataset", False)
            #self.real_data_box.setEnabled(False)
        self.real_data_box.stateChanged.connect(lambda state, sender=self.real_data_box: self.update_loggers(state, sender))
       
        if self.real_data_box.isChecked():
            self.fileButton.setEnabled(True)
        else:
            self.fileButton.setEnabled(False)
            
        self.fileButton.clicked.connect(self.load_real_dataset)        
        load_files_layout.addWidget(self.real_data_box, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        load_files_layout.addWidget(self.fileButton, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.generation_standard = QRadioButton("Configuration File", self.generation)        
        self.generation_custom = QRadioButton("Custom", self)
        
        if self.interface_params["generation_mode"] == "standard":
            self.generation_standard.setChecked(True)
            self.generation_custom.setChecked(False)
        else:
            self.generation_custom.setChecked(True)
            self.generation_standard.setChecked(False)
            
        mode_layout.addWidget(self.generation_standard, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        mode_layout.addWidget(self.generation_custom, alignment=Qt.AlignHCenter | Qt.AlignVCenter)  
            
        seed_layout = QHBoxLayout()
        seed_label = QLabel("Seed:")
        seed_layout.addWidget(seed_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.seed_edit = InterfaceUtils.create_linedit(str(self.generation_params["seed"]), "seed", QtGui.QIntValidator(1, 10000000), None)
        self.seed_edit.setMaximumWidth(50)
        seed_layout.addWidget(self.seed_edit, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        
        logger_box = InterfaceUtils.create_checkbox("Log Data", "log_data", self.generation_params["logger_active"])
        logger_box.stateChanged.connect(lambda state, sender=logger_box: self.update_loggers(state, sender))
    
        mode_layout.addLayout(seed_layout)
        load_files_layout.addWidget(logger_box, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        other_options_layout = QHBoxLayout()
        debug_label = QLabel("Debug:")
        load_files_layout.addWidget(debug_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.debug_toggle = InterfaceUtils.create_toogle(self.generation_params["debug"])
        self.debug_toggle.stateChanged.connect(self.pick_debug_method)
        load_files_layout.addWidget(self.debug_toggle, alignment=Qt.AlignLeft | Qt.AlignVCenter) 
                
        format_layout = QHBoxLayout()
        format_label = QLabel("Output Format:")
        format_layout.addWidget(format_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.format_options = InterfaceUtils.create_combox(["CSV", "EXCEL"])
        self.format_options.currentIndexChanged.connect(self.change_file_format)
        format_layout.addWidget(self.format_options, alignment=Qt.AlignLeft | Qt.AlignVCenter) 
        other_options_layout.addLayout(format_layout)
        
        source_data_layout = QHBoxLayout()
        source_label = QLabel("Source Data:")
        source_data_layout.addWidget(source_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.source_options = InterfaceUtils.create_combox(["DATABASE", "EXCEL", "CSV"])
        self.source_options.setCurrentIndex(2)
        self.source_options.currentIndexChanged.connect(self.pick_source_data)
        source_data_layout.addWidget(self.source_options, alignment=Qt.AlignLeft | Qt.AlignVCenter) 
        other_options_layout.addLayout(source_data_layout)
        
        generation_layout.addLayout(load_files_layout)
        generation_layout.addLayout(mode_layout)
        generation_layout.addLayout(other_options_layout)
    
    def load_team_widgets(self):
        """
        Customizes the operators in each team and other features. The "Operators" button opens another window.

        Returns
        -------
        None.
        
        """
        
        team_configs_layout = QHBoxLayout()
        self.teams_configs = InterfaceUtils.create_groupbox(self, "Team Configurations:", team_configs_layout, self.features_font, False)
        
        subfamily_prob_layout = QHBoxLayout()
        analyst_subfamily_label = QLabel("Subfamily Probability:")
        subfamily_prob_layout.addWidget(analyst_subfamily_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
        
        analyst_subfamily_spin = InterfaceUtils.create_doublespin(self, 0, 1, 0.01, self.treatment_params["analyst_subfamily_action_probability"])
        analyst_subfamily_spin.valueChanged.connect(self.update_analyst_same_subfamily_action_prob)
        subfamily_prob_layout.addWidget(analyst_subfamily_spin, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
            
        same_analyst_action_layout = QHBoxLayout()
        same_analyst_action_label = QLabel("Same action Probability:")
        same_analyst_action_layout.addWidget(same_analyst_action_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
        
        same_analyst_action_spin = InterfaceUtils.create_doublespin(self, 0, 1, 0.01, self.treatment_params["analyst_same_action_probability"])
        same_analyst_action_spin.valueChanged.connect(self.update_analyst_same_action_prob)
        same_analyst_action_layout.addWidget(same_analyst_action_spin, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        # Team Allocation Type QCheckBox
        users_settings = InterfaceUtils.create_checkbox("Reset Analysts Data", "reset_analysts", self.generation_params["reset_analysts_data"])
        users_settings.stateChanged.connect(lambda state, sender=users_settings: self.update_loggers(state, sender))
        
        action_layout = QVBoxLayout()
        action_layout.addLayout(subfamily_prob_layout) 
        action_layout.addLayout(same_analyst_action_layout)
        action_layout.addWidget(users_settings, alignment=Qt.AlignHCenter | Qt.AlignRight)
        team_configs_layout.addLayout(action_layout) 
        
        # Analysts Window
        analysts_button = QPushButton("Operators", self) 
        analysts_button.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        analysts_button.clicked.connect(lambda:self.build_new_subwindow("Operators", "Cybersecurity"))
        team_configs_layout.addWidget(analysts_button,alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.generation_standard.toggled.connect(self.pick_generation_method)
        self.generation_custom.toggled.connect(self.pick_generation_method)
    
    def load_ticket_widgets(self, parent):
        """
        Customizes the ticket generation (number, start date and end date, growth, seasonality, among other features).

        Parameters
        ----------
        parent : QTabWidget
            Parent tab widget.

        Returns
        -------
        QWidget
            Tab Widget.

        """   
        self.ticketTab = QWidget()
        self.ticketTab.setEnabled(False)

        date_layout = QVBoxLayout()
        
        grid = QGridLayout() 
        date_layout.addLayout(grid)

        ticket_layout = QHBoxLayout()
        ticket_label = QLabel("Ticket Number:", self)
        self.ticket_number = InterfaceUtils.create_linedit(str(self.generation_params['n_tickets']), "n_tickets", QtGui.QIntValidator(1, 10000000), self.features_font)
        self.ticket_number.editingFinished.connect(lambda: self.check_input(self.ticket_number))
        
        ticket_layout.addWidget(ticket_label, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        ticket_layout.addWidget(self.ticket_number, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        
        date_layout_init = QHBoxLayout()
        date_init = QLabel("Initial:", self)
        self.date_init_input = InterfaceUtils.create_datetimedit(datetime.strptime(self.generation_params["start_date"], '%d-%m-%Y %H:%M:%S'), "dd-MM-yyyy HH:mm:ss", self.features_font, True)
        self.date_init_input.dateTimeChanged.connect(lambda: self.update_ticket_dates("initial datetime")) 
        
        date_layout_init.addWidget(date_init, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        date_layout_init.addWidget(self.date_init_input, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        
        date_layout_end = QHBoxLayout()
        date_end = QLabel("End:", self)
        self.date_end_input = InterfaceUtils.create_datetimedit(datetime.strptime(self.generation_params["end_date"], '%d-%m-%Y %H:%M:%S'), "dd-MM-yyyy HH:mm:ss", self.features_font, True)
        self.date_end_input.dateTimeChanged.connect(lambda: self.update_ticket_dates("end datetime")) 
        
        date_layout_end.addWidget(date_end, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        date_layout_end.addWidget(self.date_end_input, alignment = Qt.AlignHCenter | Qt.AlignVCenter)   
        
        ticket_escalation_layout = QHBoxLayout()
        ticket_escalation_label = QLabel("Escalate Tickets:")
        self.ticket_escalation_toggle = InterfaceUtils.create_toogle(self.generation_params["ticket_escalation_selector"])
        
        ticket_escalation_layout.addWidget(ticket_escalation_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        ticket_escalation_layout.addWidget(self.ticket_escalation_toggle, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
        
        escalation_widget = QWidget()
        escalation_layout = QHBoxLayout()
        escalation_widget.setLayout(escalation_layout)
        escalate_label = QLabel("Escalation Probability:", self)
        
        self.escalation_slider = InterfaceUtils.create_doublespin(self, 0, 0.5, 0.1, self.generation_params["escalate_rate_percentage"])
        self.escalation_slider.setMaximumWidth(100)
        self.escalation_slider.valueChanged.connect(self.update_escalation_rate)
        
        escalation_layout.addWidget(escalate_label, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        escalation_layout.addWidget(self.escalation_slider, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.ticket_escalation_toggle.stateChanged.connect(lambda:self.pick_escalation_method(escalation_widget))
        
        ticket_season_layout = QHBoxLayout()
        ticket_season_label = QLabel("Ticket Seasonality:")
        self.ticket_season_toggle = InterfaceUtils.create_toogle(self.generation_params["ticket_seasonality_selector"])
        
        ticket_season_layout.addWidget(ticket_season_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        ticket_season_layout.addWidget(self.ticket_season_toggle, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
        
        ticket_growth_layout = QHBoxLayout()
        ticket_growth_label = QLabel("Ticket Growth:")
        self.ticket_growth_toggle = InterfaceUtils.create_toogle(self.generation_params["ticket_growth_selector"])
        self.ticket_growth_doublespin = InterfaceUtils.create_doublespin(self, -0.9, 0.9, 0.05, self.generation_params["ticket_growth_rate"])
        if self.generation_params["ticket_growth_rate"] == 0:
            self.ticket_growth_doublespin.setEnabled(False)
        self.ticket_growth_doublespin.valueChanged.connect(self.update_growth_rate)
    
        ticket_growth_layout.addWidget(ticket_growth_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        ticket_growth_layout.addWidget(self.ticket_growth_toggle, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        ticket_growth_layout.addWidget(self.ticket_growth_doublespin, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.ticket_season_toggle.stateChanged.connect(self.pick_ticket_seasonality)
        self.ticket_growth_toggle.stateChanged.connect(self.pick_ticket_growth)

        grid.addLayout(ticket_layout, 0, 0)
        grid.addLayout(date_layout_init, 1, 0)
        grid.addLayout(date_layout_end, 1, 1)
        grid.addLayout(ticket_escalation_layout, 2, 0)
        grid.addWidget(escalation_widget, 2, 1)
        grid.addLayout(ticket_season_layout, 3, 0)
        grid.addLayout(ticket_growth_layout, 3, 1)

        self.ticketTab.setLayout(date_layout)
        
        return self.ticketTab 
    
    def load_family_widgets(self):
        """
        Customizes the family generation (can be by default or customized). The number of families, minimum number of subfamilies, maximum number of subfamilies, week and time distributions, and other features can be personalized.

        Returns
        -------
        QScrollArea
            Scroll area in the main window.

        """
        self.familyTab = QWidget()
        self.familyTab.setEnabled(False)        
        family_default_layout = QVBoxLayout()
        
        self.family_scroll = QScrollArea()
        self.family_scroll.setWidgetResizable(True)
        self.family_scroll.setWidget(self.familyTab)

        default_layout = QHBoxLayout() 
        family_default = InterfaceUtils.create_radiobox("Default", self.generation_params["use_default_family"])
        family_default.toggled.connect(lambda:self.pick_family_method(family_default))
        default_layout.addWidget(family_default, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        plot_layout = QHBoxLayout()
        plot_label = QLabel("Plots:")
        self.plot_toggle = InterfaceUtils.create_toogle(False)
        self.plot_toggle.stateChanged.connect(self.print_plots)
        
        plot_layout.addWidget(plot_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        plot_layout.addWidget(self.plot_toggle, alignment=Qt.AlignLeft) 
        
        family_season_layout = QHBoxLayout()
        family_season_label = QLabel("Family Seasonality:")
        self.family_season_toggle = InterfaceUtils.create_toogle(self.generation_params["family_seasonality_selector"])
        self.family_season_toggle.stateChanged.connect(self.pick_family_seasonality)
        
        family_season_layout.addWidget(family_season_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        family_season_layout.addWidget(self.family_season_toggle, alignment=Qt.AlignLeft) 
        
        replication_layout = QHBoxLayout()
        similar_tickets_layout = QHBoxLayout()
        similar_tickets_layout.setContentsMargins(80, 0, 0, 0)
        similar_tickets_label = QLabel("Similar Tickets Detection:")
        
        self.similar_tickets_toggle = InterfaceUtils.create_toogle(self.treatment_params["ticket_similarity_selector"])
        self.similar_tickets_toggle.stateChanged.connect(self.pick_ticket_similarity)
        
        similar_tickets_layout.addWidget(similar_tickets_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        similar_tickets_layout.addWidget(self.similar_tickets_toggle, alignment=Qt.AlignLeft) 
        
        verify_tickets_layout = QHBoxLayout()
        verify_tickets_layout.setContentsMargins(80, 0, 0, 0)
        verify_tickets_label = QLabel("Verify Tickets:")
        self.verify_tickets_toggle = InterfaceUtils.create_toogle(self.treatment_params["ticket_verification_selector"])
        self.verify_tickets_toggle.stateChanged.connect(self.pick_ticket_verification_method)
        
        verify_tickets_layout.addWidget(verify_tickets_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        verify_tickets_layout.addWidget(self.verify_tickets_toggle, alignment=Qt.AlignLeft) 
        
        default_layout.addLayout(plot_layout)
        default_layout.addLayout(family_season_layout)
        replication_layout.addLayout(similar_tickets_layout)
        replication_layout.addLayout(verify_tickets_layout)
        family_default_layout.addLayout(default_layout)
        family_default_layout.addLayout(replication_layout)
        
        family_layout = QHBoxLayout() 
        family_label = QLabel("Number of Families:", self)
        self.family_number = InterfaceUtils.create_linedit(str(self.generation_params['families_number']), "family_number", QtGui.QIntValidator(0, 100), self.features_font)
        self.family_number.editingFinished.connect(lambda: self.check_input(self.family_number))
        
        family_layout.addWidget(family_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        family_layout.addWidget(self.family_number, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        family_default_layout.addLayout(family_layout)
        
        min_sub_family_layout = QHBoxLayout() 
        min_subfamily_label = QLabel("Minimum Number of SubFamilies:", self)
        self.min_subfamily_number = InterfaceUtils.create_linedit(str(self.generation_params['minsubfamilies_number']), "minimum_subFamilies", QtGui.QIntValidator(0, 10), self.features_font)
        self.min_subfamily_number.editingFinished.connect(lambda: self.check_input(self.min_subfamily_number))
        
        min_sub_family_layout.addWidget(min_subfamily_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        min_sub_family_layout.addWidget(self.min_subfamily_number, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        family_default_layout.addLayout(min_sub_family_layout)
        
        max_sub_family_layout = QHBoxLayout() 
        max_subfamily_label = QLabel("Maximum Number of SubFamilies:", self)
        self.max_subfamily_number = InterfaceUtils.create_linedit(str(self.generation_params['maxsubfamilies_number']), "maximum_subFamilies", QtGui.QIntValidator(0, 100), self.features_font)
        self.max_subfamily_number.editingFinished.connect(lambda: self.check_input(self.max_subfamily_number))
        
        max_sub_family_layout.addWidget(max_subfamily_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        max_sub_family_layout.addWidget(self.max_subfamily_number, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        family_default_layout.addLayout(max_sub_family_layout)
        
        selectable_families_layout = QHBoxLayout()
        selectable_families_label = QLabel("Types of Families:")
        self.selectable_families_combo = CheckableComboBox("families", int(self.family_number.text()))
        self.selectable_families_combo.setEnabled(False)

        for i in range(len(string.ascii_uppercase)):
            self.selectable_families_combo.addItem(string.ascii_uppercase[i])
            item = self.selectable_families_combo.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)
        
        selectable_families_layout.addWidget(selectable_families_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        selectable_families_layout.addWidget(self.selectable_families_combo, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        family_default_layout.addLayout(selectable_families_layout)
        
        selected_families_layout = QHBoxLayout()
        selected_families_label = QLabel("Selected Families:")
        self.selected_families = QLabel("Random")
        
        selected_families_layout.addWidget(selected_families_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        selected_families_layout.addWidget(self.selected_families, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        family_default_layout.addLayout(selected_families_layout)
        
        self.selectable_families_combo.activated.connect(self.add_family)   
        
        coordinated_layout = QVBoxLayout()   
        self.coordinated_attacks_groupbox = InterfaceUtils.create_groupbox(self, "Similarity Detection:", coordinated_layout, self.features_font, self.treatment_params["ticket_similarity_selector"])

        min_occurences_layout = QHBoxLayout() 
        min_occurences_label = QLabel("Minimum Number of Occurences:", self)
        self.min_occurences_number = InterfaceUtils.create_linedit(str(self.generation_params['min_coordinated_attack']), "minimum_attack_occurences", QtGui.QIntValidator(0, 4), self.features_font)
        self.min_occurences_number.editingFinished.connect(lambda: self.check_input(self.min_occurences_number))
        
        min_occurences_layout.addWidget(min_occurences_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        min_occurences_layout.addWidget(self.min_occurences_number, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        coordinated_layout.addLayout(min_occurences_layout)
        
        max_occurences_layout = QHBoxLayout() 
        max_occurences_label = QLabel("Maximum Number of Occurences:", self)
        self.max_occurences_number = InterfaceUtils.create_linedit(str(self.generation_params['max_coordinated_attack']), "maximum_attack_occurences", QtGui.QIntValidator(0, 10), self.features_font)
        self.max_occurences_number.editingFinished.connect(lambda: self.check_input(self.max_occurences_number))
        
        max_occurences_layout.addWidget(max_occurences_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        max_occurences_layout.addWidget(self.max_occurences_number, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        coordinated_layout.addLayout(max_occurences_layout)
        
        min_attack_timerange_layout = QHBoxLayout()
        min_attack_timerange_label = QLabel("Minimum range time detection:", self)
        
        min_attack_timerange_slider_layout = QHBoxLayout()
        min_attack_timerange_slider = InterfaceUtils.create_slider(Qt.Horizontal, 20, 59, self.generation_params["min_coordinated_attack_minutes"], 1)
        min_attack_timerange_slider.setFixedWidth(200)
        min_attack_timerange_rate_label = QLabel(f'{min_attack_timerange_slider.value()} minutes', self)        
        min_attack_timerange_rate_label.setObjectName('min_time_detection')
        
        min_attack_timerange_slider_layout.addWidget(min_attack_timerange_slider, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        min_attack_timerange_slider_layout.addWidget(min_attack_timerange_rate_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        min_attack_timerange_layout.addWidget(min_attack_timerange_label, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        min_attack_timerange_layout.addLayout(min_attack_timerange_slider_layout)
        coordinated_layout.addLayout(min_attack_timerange_layout)
        
        max_attack_timerange_layout = QHBoxLayout()
        max_attack_timerange_label = QLabel("Maximum range time detection:", self)
        
        max_attack_timerange_slider_layout = QHBoxLayout()
        max_attack_timerange_slider = InterfaceUtils.create_slider(Qt.Horizontal, 60, 120, self.generation_params["max_coordinated_attack_minutes"], 1)
        max_attack_timerange_slider.setFixedWidth(200)
        max_attack_timerange_rate_label = QLabel(f'{max_attack_timerange_slider.value()} minutes', self)        
        max_attack_timerange_rate_label.setObjectName('max_time_detection')
       
        max_attack_timerange_slider_layout.addWidget(max_attack_timerange_slider, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        max_attack_timerange_slider_layout.addWidget(max_attack_timerange_rate_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        max_attack_timerange_layout.addWidget(max_attack_timerange_label, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        max_attack_timerange_layout.addLayout(max_attack_timerange_slider_layout)
        coordinated_layout.addLayout(max_attack_timerange_layout)
        
        min_attack_timerange_slider.sliderReleased.connect(lambda: self.update_detection_timerange(min_attack_timerange_slider, min_attack_timerange_rate_label))
        max_attack_timerange_slider.sliderReleased.connect(lambda: self.update_detection_timerange(max_attack_timerange_slider, max_attack_timerange_rate_label))
        
        distribution_layout = QHBoxLayout()  
        self.distribution_groupbox = InterfaceUtils.create_groupbox(self, "Distribution:", distribution_layout, self.features_font, False)
        self.family_distribution_normal = InterfaceUtils.create_radiobox("Normal", True)
        self.family_distribution_normal.toggled.connect(lambda:self.pick_distribution_method(self.family_distribution_normal))
        self.family_distribution_uniform = InterfaceUtils.create_radiobox("Uniform", False)
        self.family_distribution_uniform.toggled.connect(lambda:self.pick_distribution_method(self.family_distribution_uniform))
        
        distribution_layout.addWidget(self.family_distribution_normal, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        distribution_layout.addWidget(self.family_distribution_uniform, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        family_default_layout.addWidget(self.distribution_groupbox)
       
        family_grid = QGridLayout()
        
        time_layout = QVBoxLayout()
        self.time_generation = InterfaceUtils.create_groupbox(self, "Time Probabilities:", time_layout, self.features_font, False)
        self.time_equal = InterfaceUtils.create_radiobox("Equal in all hours", True)
        self.time_equal.toggled.connect(self.pick_time_method)
        time_layout.addWidget(self.time_equal, alignment=Qt.AlignHCenter | Qt.AlignVCenter)

        time_day_light = QLabel("Higher on Daylight", self)
        time_day_light_layout = QHBoxLayout()
        self.spin_time_day_light = InterfaceUtils.create_doublespin(self, 0, 1, 0.01, self.generation_params["family_time_4h"][2]['prob'] + self.generation_params["family_time_4h"][3]['prob'] + self.generation_params["family_time_4h"][4]['prob'])
        self.spin_time_day_light.setEnabled(False)
        self.spin_time_day_light.valueChanged.connect(lambda:self.update_families_time_probabilities(time_day_light, self.spin_time_day_light))
        
        time_day_light_layout.addWidget(time_day_light)
        time_day_light_layout.addWidget(self.spin_time_day_light)
        
        time_night_light_layout = QHBoxLayout()
        time_night_light = QLabel("Higher on Night", self)
        self.spin_time_night_light = InterfaceUtils.create_doublespin(self, 0, 1, 0.01, self.generation_params["family_time_4h"][0]['prob'] + self.generation_params["family_time_4h"][1]['prob'] + self.generation_params["family_time_4h"][5]['prob'])
        self.spin_time_night_light.setEnabled(False)
        self.spin_time_night_light.valueChanged.connect(lambda:self.update_families_time_probabilities(time_night_light, self.spin_time_night_light))
        
        time_night_light_layout.addWidget(time_night_light)
        time_night_light_layout.addWidget(self.spin_time_night_light)
        time_layout.addLayout(time_day_light_layout)
        time_layout.addLayout(time_night_light_layout)
        family_grid.addWidget(self.time_generation, 0, 0)
        
        # Week
        week_family_layout = QVBoxLayout()
        self.week_generation = InterfaceUtils.create_groupbox(self, "Week Probabilities:", week_family_layout, self.features_font, False)
        self.week_equal = InterfaceUtils.create_radiobox("Equal in all days", True)
        self.week_equal.toggled.connect(lambda:self.pick_week_method)
        week_family_layout.addWidget(self.week_equal, alignment=Qt.AlignHCenter | Qt.AlignVCenter)

        week_layout = QHBoxLayout()
        week_label = QLabel("Higher on Weekdays", self)  
        self.spin_week = InterfaceUtils.create_doublespin(self, 0, 1, 0.01, self.generation_params["week_time"][0]['prob'] + self.generation_params["week_time"][1]['prob'] + self.generation_params["week_time"][2]['prob'] + self.generation_params["week_time"][3]['prob'] + self.generation_params["week_time"][4]['prob'])
        self.spin_week.setEnabled(False)
        self.spin_week.valueChanged.connect(lambda:self.update_families_week_probabilities(week_label, self.spin_week))
        
        week_layout.addWidget(week_label)
        week_layout.addWidget(self.spin_week)
        
        weekend_layout = QHBoxLayout()
        weekend_label = QLabel("Higher on Weekend", self)
        self.spin_weekend = InterfaceUtils.create_doublespin(self, 0, 1, 0.01, self.generation_params["week_time"][5]['prob'] + self.generation_params["week_time"][6]['prob'])
        self.spin_weekend.setEnabled(False)
        self.spin_weekend.valueChanged.connect(lambda:self.update_families_week_probabilities(weekend_label, self.spin_weekend))
        
        weekend_layout.addWidget(weekend_label)
        weekend_layout.addWidget(self.spin_weekend)
        week_family_layout.addLayout(week_layout)
        week_family_layout.addLayout(weekend_layout)   
        family_grid.addWidget(self.week_generation, 0, 1)
        family_default_layout.addLayout(family_grid)
        family_default_layout.addWidget(self.coordinated_attacks_groupbox)
        self.familyTab.setLayout(family_default_layout)
        
        return self.family_scroll
    
    def load_technique_widgets(self):
        """
        Customizes the properties related to techniques used for ticket treatment (number, minimum subtechniques, maximum subtechniques, among other features).    

        Returns
        -------
        techniques_scroll : QScrollArea
            Scroll area in the main window.

        """
        self.techniquesTab = QWidget()
        self.techniquesTab.setEnabled(False)
        
        techniques_scroll = QScrollArea()
        techniques_scroll.setWidgetResizable(True)
        techniques_scroll.setWidget(self.techniquesTab)
        techniques_configs_layout = QVBoxLayout()
        
        technique_layout = QHBoxLayout()  
        technique_label = QLabel("Number:", self)
        self.technique_number = InterfaceUtils.create_linedit(str(self.generation_params['techniques_number']), "techniques_number", QtGui.QIntValidator(1, 62), self.features_font)
        self.technique_number.textChanged.connect(lambda: self.check_input(self.technique_number))
        
        technique_layout.addWidget(technique_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        technique_layout.addWidget(self.technique_number, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        duration_season_layout = QHBoxLayout()
        duration_season_label = QLabel("Duration Seasonality:")
        self.duration_season_toggle = InterfaceUtils.create_toogle(self.generation_params["techniques_seasonality_selector"])
        
        duration_season_layout.addWidget(duration_season_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        duration_season_layout.addWidget(self.duration_season_toggle, alignment=Qt.AlignHCenter | Qt.AlignVCenter) 
        
        # Min subTechniques
        min_subtechnique_layout = QHBoxLayout()
        min_subtechnique_label = QLabel("Sub techniques minimum:", self)
        min_subtechnique_layout.addWidget(min_subtechnique_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.min_subtechnique_number = InterfaceUtils.create_linedit(str(self.generation_params['minsubtechniques_number']), "min_subtechnique", QtGui.QIntValidator(0, 30), self.features_font)
        self.min_subtechnique_number.setEnabled(False)
        self.min_subtechnique_number.editingFinished.connect(lambda: self.check_input(self.min_subtechnique_number))
        min_subtechnique_layout.addWidget(self.min_subtechnique_number, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        min_subtechniques_dur_layout = QHBoxLayout()
        min_subtechniques_dur_label = QLabel("Sub techniques minimum rate:", self)
        min_subtechniques_dur_layout.addWidget(min_subtechniques_dur_label, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        temp_layout = QHBoxLayout()
        
        self.min_subtechnique_slider = InterfaceUtils.create_slider(Qt.Horizontal, 50, 199, self.generation_params["min_subtechnique_rate"], 1)
        self.min_subtechnique_slider.setFixedWidth(200)
        temp_layout.addWidget(self.min_subtechnique_slider, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        min_subtechniques_dur_rate_label = QLabel(f'Rate: {self.min_subtechnique_slider.value()} %', self)        
        min_subtechniques_dur_rate_label.setObjectName('min_sub')
        temp_layout.addWidget(min_subtechniques_dur_rate_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        min_subtechniques_dur_layout.addLayout(temp_layout)
        
        min_subtechniques_cost_layout = QHBoxLayout()
        min_subtechniques_cost_label = QLabel("Sub techniques minimum cost:", self)
        min_subtechniques_cost_layout.addWidget(min_subtechniques_cost_label, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        temp_layout = QHBoxLayout()
        
        self.min_subtechnique_cost_slider = InterfaceUtils.create_slider(Qt.Horizontal, 1, 5, self.generation_params["min_subtechnique_cost"], 1)
        self.min_subtechnique_cost_slider.setFixedWidth(200)
        temp_layout.addWidget(self.min_subtechnique_cost_slider, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        min_subtechniques_cost_rate_label = QLabel(f'Cost: {self.min_subtechnique_cost_slider.value()}', self)        
        min_subtechniques_cost_rate_label.setObjectName('min_sub_cost')
        temp_layout.addWidget(min_subtechniques_cost_rate_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        min_subtechniques_cost_layout.addLayout(temp_layout)
        
        # Max subTechniques
        max_subtechnique_layout = QHBoxLayout()
        max_subtechnique_label = QLabel("Sub techniques maximum:", self)
        max_subtechnique_layout.addWidget(max_subtechnique_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.max_subtechnique_number = InterfaceUtils.create_linedit(str(self.generation_params['maxsubtechniques_number']), "max_subtechnique", QtGui.QIntValidator(0, 100), self.features_font)
        self.max_subtechnique_number.setEnabled(False)
        self.max_subtechnique_number.editingFinished.connect(lambda: self.check_input(self.max_subtechnique_number))
        max_subtechnique_layout.addWidget(self.max_subtechnique_number, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        max_subtechniques_cost_layout = QHBoxLayout()
        max_subtechniques_cost_label = QLabel("Sub techniques maximum cost:", self)
        max_subtechniques_cost_layout.addWidget(max_subtechniques_cost_label, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        temp_layout = QHBoxLayout()
        
        self.max_subtechnique_cost_slider = InterfaceUtils.create_slider(Qt.Horizontal, 6, 9, self.generation_params["max_subtechnique_cost"], 1)
        self.max_subtechnique_cost_slider.setFixedWidth(200)
        temp_layout.addWidget(self.max_subtechnique_cost_slider, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        max_subtechniques_cost_rate_label = QLabel(f'Cost: {self.max_subtechnique_cost_slider.value()}', self)
        max_subtechniques_cost_rate_label.setObjectName('max_sub_cost')
        self.min_subtechnique_cost_slider.sliderReleased.connect(lambda: self.update_subtechnique_cost(self.min_subtechnique_cost_slider, min_subtechniques_cost_rate_label))
        self.max_subtechnique_cost_slider.sliderReleased.connect(lambda: self.update_subtechnique_cost(self.max_subtechnique_cost_slider, max_subtechniques_cost_rate_label))
        temp_layout.addWidget(max_subtechniques_cost_rate_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        max_subtechniques_cost_layout.addLayout(temp_layout)
        
        max_subtechniques_dur_layout = QHBoxLayout()
        max_subtechniques_dur_label = QLabel("Sub techniques maximum rate:", self)
        max_subtechniques_dur_layout.addWidget(max_subtechniques_dur_label, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
        temp_layout = QHBoxLayout()
        
        self.max_subtechnique_slider = InterfaceUtils.create_slider(Qt.Horizontal, 51, 200, self.generation_params["max_subtechnique_rate"], 1)
        self.max_subtechnique_slider.setFixedWidth(200)
        temp_layout.addWidget(self.max_subtechnique_slider, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        max_subtechniques_dur_rate_label = QLabel(f'Rate: {self.max_subtechnique_slider.value()} %', self)
        max_subtechniques_dur_rate_label.setObjectName('max_sub')
        self.min_subtechnique_slider.sliderReleased.connect(lambda: self.update_subtechnique_rate(self.min_subtechnique_slider, min_subtechniques_dur_rate_label))
        self.max_subtechnique_slider.sliderReleased.connect(lambda: self.update_subtechnique_rate(self.max_subtechnique_slider, max_subtechniques_dur_rate_label))
        
        temp_layout.addWidget(max_subtechniques_dur_rate_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        max_subtechniques_dur_layout.addLayout(temp_layout)
        
        self.duration_season_toggle.stateChanged.connect(self.update_techniques_seasonality)
        
        techniques_configs_layout.addLayout(technique_layout)
        techniques_configs_layout.addLayout(duration_season_layout)
        techniques_configs_layout.addLayout(min_subtechnique_layout)
        techniques_configs_layout.addLayout(min_subtechniques_cost_layout)
        techniques_configs_layout.addLayout(min_subtechniques_dur_layout)
        
        techniques_configs_layout.addLayout(max_subtechnique_layout)
        techniques_configs_layout.addLayout(max_subtechniques_cost_layout)
        techniques_configs_layout.addLayout(max_subtechniques_dur_layout)
       
        self.techniquesTab.setLayout(techniques_configs_layout)
        
        return techniques_scroll
    
    def load_learning_widgets(self):
        """
        Customized the minimum and maximun number of events for operator learning (helps determining when operators should improve their learning rate).

        Returns
        -------
        learning_scroll : QScrollArea
            Scroll area in the main window.

        """
        self.learningTab = QWidget()
        self.learningTab.setEnabled(False)
        
        learning_scroll = QScrollArea()
        learning_scroll.setWidgetResizable(True)
        learning_scroll.setWidget(self.learningTab)
        learning_configs_layout = QVBoxLayout()
    
        # Min subTechniques
        min_counter_layout = QHBoxLayout()
        min_counter_label = QLabel("Min counter:", self)
        min_counter_layout.addWidget(min_counter_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.min_counter_number = InterfaceUtils.create_linedit(str(self.treatment_params['min_learning_counter']), "min_counter", QtGui.QIntValidator(), self.features_font)
        self.min_counter_number.setEnabled(False)
        self.min_counter_number.editingFinished.connect(lambda: self.check_input(self.min_counter_number))
        min_counter_layout.addWidget(self.min_counter_number, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        # Max subTechniques
        max_counter_layout = QHBoxLayout()
        max_counter_label = QLabel("Max counter:", self)
        max_counter_layout.addWidget(max_counter_label, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        self.max_counter_number = InterfaceUtils.create_linedit(str(self.treatment_params['max_learning_counter']), "max_counter", QtGui.QIntValidator(), self.features_font)
        self.max_counter_number.setEnabled(False)
        self.max_counter_number.editingFinished.connect(lambda: self.check_input(self.max_counter_number))
        max_counter_layout.addWidget(self.max_counter_number, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        
        learning_configs_layout.addLayout(min_counter_layout)
        learning_configs_layout.addLayout(max_counter_layout)
        self.learningTab.setLayout(learning_configs_layout)
        
        return learning_scroll
    
    def load_outlier_widgets(self, main_layout):
        """
        Customizes widgets related to outlier (impact and frequency)-    

        Parameters
        ----------
        main_layout : QVBoxLayout
            Windoow main layout.

        Returns
        -------
        None.

        """
        outlier_layout = QHBoxLayout()
        self.outlier_groupbox = InterfaceUtils.create_groupbox(self, "Outlier Configurations:", outlier_layout, self.features_font, self.interface_params["outlier_selector"])

        outlier = QLabel("Extra Action Cost:", self)
        outlier.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        outlier_layout.addWidget(outlier)
        
        outlier_spin = InterfaceUtils.create_doublespin(self, 0, 1, 0.01, self.generation_params["outlier_cost"])
        outlier_spin.valueChanged.connect(self.update_outlier_value)
        outlier_layout.addWidget(outlier_spin, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
         
        outlier_rate_layout = QVBoxLayout()
        outlier_rate_layout.setContentsMargins(0, 25, 0, 0)
        
        self.outlier_slider = InterfaceUtils.create_slider(Qt.Horizontal, 1, 20, self.generation_params["outlier_rate"], 1)
        self.outlier_slider.setFixedWidth(200)
        self.outlier_slider.sliderReleased.connect(self.update_outlier_rate)
        outlier_rate_layout.addWidget(self.outlier_slider, alignment = Qt.AlignHCenter | Qt.AlignBottom)
        
        self.outlier_rate_output = QLabel(f'Frequency rate: {self.generation_params["outlier_rate"]} %', self)
        self.outlier_rate_output.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.outlier_rate_output.setFont(self.features_font)
        outlier_rate_layout.addWidget(self.outlier_rate_output, alignment = Qt.AlignHCenter | Qt.AlignTop)
        
        outlier_layout.addLayout(outlier_rate_layout)
        main_layout.addWidget(self.outlier_groupbox)
    
    def load_generate_button(self):
        """
        Button for dataset generation.

        Returns
        -------
        report_layout : QHBoxLayout
            Layout of the generation button.

        """          
        bar_layout = QVBoxLayout()

        self.generate_button = InterfaceUtils.create_button(self, "Generate", "generateButton", "ready")
        self.generate_button.clicked.connect(self.check_generation)
        bar_layout.addWidget(self.generate_button, alignment = Qt.AlignHCenter | Qt.AlignVCenter)
       
        self.progress_report = QLabel("", self)
        self.progress_report.setFont(QtGui.QFont('Arial', 11)) 
        self.progress_report.setFont(self.features_font)
        self.progress_report.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)   
        bar_layout.addWidget(self.progress_report)
        
        report_layout = QHBoxLayout()
        report_layout.addLayout(bar_layout)
        
        return report_layout
    
    def add_family(self):
        """
        Adds families to comboBox.

        Returns
        -------
        None.

        """
        families = ""
        counter = 0
        
        for i in range(self.selectable_families_combo.count()):
            if self.selectable_families_combo.item_checked(i):     
                if families == "":
                    families = f'{families}{self.selectable_families_combo.itemText(i)}'
                elif families != "" and counter < self.selectable_families_combo.limit:
                    families = f'{families} - {self.selectable_families_combo.itemText(i)}'
                counter += 1
                
        if families == "":
            families = "Random"
               
        print("fam", families)     
        self.selected_families.setText(families)
                    
    # Sets the suspicious counters in the Options Tab
    def set_suspicious_countries(self, country, layout, country_idx, initial):
        """
        Configures the suspicious countries in the Options Tab.

        Parameters
        ----------
        country : strs
            Country selected.
        layout : QGridLayout
            Grid layout of the suspicious countries.
        country_idx : int
            Index of the country selected.
        initial : bool
            If coutnrie(s) is/are set at the start of the setup or not. 

        Returns
        -------
        None.

        """
        self.generation_params["suspicious_countries"][country] = {}

        country_label = QLabel("Country:" , self) 
        country_label.setFont(self.features_font)
        country_widget = QLabel(country , self) 
          
        country_start_date_label = QLabel("Start Date:", self)
        country_start_date_label.setFont(self.features_font)
        if initial:
            country_start_date = QLabel(str(self.init_suspicious_countries[country]['start']) , self) 
        else:
            country_start_date = QLabel(str(self.sus_countries_start_time.text()) , self) 
            
        country_end_date_label = QLabel("End Date:", self)
        country_end_date_label.setFont(self.features_font)
        if initial:
            country_end_date = QLabel(str(self.init_suspicious_countries[country]['end']), self) 
        else:
            country_end_date = QLabel(str(self.sus_countries_end_time.text()), self) 

        self.generation_params["suspicious_countries"][country]['widget label country'] = country_label
        self.generation_params["suspicious_countries"][country]['widget country'] = country_widget
        self.generation_params["suspicious_countries"][country]['widget label start date'] = country_start_date_label
        self.generation_params["suspicious_countries"][country]['widget start date'] = country_start_date
        self.generation_params["suspicious_countries"][country]['widget label end date'] = country_end_date_label
        self.generation_params["suspicious_countries"][country]['widget end date'] = country_end_date

        layout.addWidget(country_label, country_idx, 0)  
        layout.addWidget(country_widget, country_idx, 1)  
        layout.addWidget(country_start_date_label, country_idx, 2)  
        layout.addWidget(country_start_date, country_idx, 3)   
        layout.addWidget(country_end_date_label, country_idx, 4)   
        layout.addWidget(country_end_date, country_idx, 5)  

    def add_suspicious_countries(self):
        """
        Adds all the suspicious countries to the suspicious countries layout.

        Returns
        -------
        None.

        """        
        keys_list = list(self.init_suspicious_countries.keys())
        for country in self.init_suspicious_countries:
            country_index = self.sus_countries_combo.findText(country)
            country_item = self.sus_countries_combo.model().item(country_index, 0)
            country_item.setCheckState(Qt.Checked)
            self.sus_countries_combo.setCurrentIndex(country_index)
            self.set_suspicious_countries(country, self.countries_grid, keys_list.index(country), True)
            
    def add_single_suspicious_country(self):
        """
        Adds a single country to the suspicious countries layout.

        Returns
        -------
        None.

        """
        country = self.sus_countries_combo.itemText(self.sus_countries_combo.currentIndex())
        keys_list = list(self.init_suspicious_countries.keys())
        keys_list.append(country)
        
        if self.sus_countries_combo.item_checked(self.sus_countries_combo.currentIndex()):   
            self.set_suspicious_countries(country, self.countries_grid, keys_list.index(country), False)
        else:
            self.remove_country(country)
    
    def update_output_params(self):
        """
        Updates the columns that the generated dataset should possess.

        Returns
        -------
        None.

        """    
        param = self.output_parameters_combo.itemText(self.output_parameters_combo.currentIndex())
        print("Param:", param)
        if self.auxiliar_dataset_params[param]:
            self.auxiliar_dataset_params[param] = False
            
        else:
            self.auxiliar_dataset_params[param] = True
        print(f'{param} is now {self.auxiliar_dataset_params[param]}')
    
    # Removes a certain country
    def remove_country(self, country):
        """
        Removes a certain country from the suspicious countries list.

        Parameters
        ----------
        country : str
            Country to be unselected.

        Returns
        -------
        None.

        """
        print(f'Country {country} was unchecked')
        self.generation_params["suspicious_countries"][country]['widget label country'].setParent(None)
        self.generation_params["suspicious_countries"][country]['widget country'].setParent(None)
        self.generation_params["suspicious_countries"][country]['widget label start date'].setParent(None)
        self.generation_params["suspicious_countries"][country]['widget start date'].setParent(None)
        self.generation_params["suspicious_countries"][country]['widget label end date'].setParent(None)
        self.generation_params["suspicious_countries"][country]['widget end date'].setParent(None)
        del(self.generation_params["suspicious_countries"][country]) 
        
    def closeTool(self):
        """
        Closes all open windows.

        Returns
        -------
        None.

        """
        for i in self.subwindows:
            i.close()       
        self.close()
    
    # Opens Teams window
    def build_new_subwindow(self, window_type, domain):
        """
        Opens a new subwindow (for the team configuration).

        Parameters
        ----------
        windowType : str
            Window type (Analysts).
        domain : str
            Generation domain (cybersecurity).

        Returns
        -------
        None.

        """    
        subwindow_found = False
        
        for i in self.subwindows:
            if i.type == window_type:
                subwindow_found = True
                if window_type == "Analysts":
                    print("The analysts window is already opened!")
                break
        
        if not subwindow_found:
            sub_window = TeamAnalystWindow(self, window_type, domain)
            sub_window.window().resize(700, 500)
            self.subwindows.append(sub_window)
            sub_window.show()
    
    def lock_dates(self, widget):
        """
        Locks the ability to change the start and end datetimes for the generation.   

        Parameters
        ----------
        widget : QWidget
            Widget responsible for the configuration of the start and end datetimes.

        Returns
        -------
        None.

        """    
        if widget.isEnabled():
            print("Dates customization disabled!") 
            widget.setEnabled(False)
            self.sus_countries_lock.setIcon(QtGui.QIcon('Resources/Icons/locked.ico'))
            self.sus_countries_lock.setIconSize(QSize(40, 40))   
        else:
            print("Dates customization enabled!")
            widget.setEnabled(True)
            self.sus_countries_lock.setIcon(QtGui.QIcon('Resources/Icons/unlocked.ico'))
            self.sus_countries_lock.setIconSize(QSize(40, 40))
    
    def change_file_format(self, file_format):
        """
        Changes the domain being analyzed (default is cybersecurity).

        Parameters
        ----------
        file_format : int
            File index.

        Returns
        -------
        None.

        """
        self.generation_params["format_selected_idx"] = file_format
        print(file_format)
        print("Variables ip selected:", str(self.format_options.currentText()))
        
    def pick_source_data(self, source_data_format):
        """
        Selects the source data of real data.

        Parameters
        ----------
        source_data_format : int
            Source data index.

        Returns
        -------
        None.

        """
        print("Source data:", self.source_options.currentText())
        print(source_data_format)
        if source_data_format == 0:
            database_window = SQLConnectionWindow()
            database_window.setGeometry(300, 300, 300, 300)
            database_window.dataSubmitted.connect(self.receive_connection)
            self.subwindows.append(database_window)
            database_window.show()
        else:
            if self.datasets_available:
                self.update_seasonality_widgets(True)
            else:
                self.update_seasonality_widgets(False)

    def receive_connection(self, conn):
        """
        Receives information from the connected database.    

        Parameters
        ----------
        conn : psycopg2
            Database connection.

        Returns
        -------
        None.

        """
        print("Received Connection Object")
        self.generation_params["ticket_seasonality"], self.generation_params["family_seasonality"], self.generation_params["family_mean_duration"], self.generation_params["family_mapping"] = Configurator.get_ticket_seasonality(self.file, True, conn, False)

    def pick_distribution_method(self, d):
        """
        Sets the distribution of families.

        Parameters
        ----------
        d : str
            Distribution picked for families.

        Returns
        -------
        None.

        """        
        if d.text() == "Normal":
            if d.isChecked() == True:
                print("Normal distributions activated!")
                self.week_generation.setEnabled(True)
                self.time_generation.setEnabled(True)            
                self.generation_params["distribution_mode"] = "normal"
        if d.text() == "Uniform":
            if d.isChecked() == True:
                print("Uniform distribution activated!")
                self.week_generation.setEnabled(False)
                self.time_generation.setEnabled(False)
                self.generation_params["distribution_mode"] = "uniform"
            
    def update_loggers(self, state, sender):
        """
        Activates/Deactivates the logger functionality.

        Parameters

        ----------
        state : int
            Logger state.
        sender : str
            Widget that required a change.

        Returns
        -------
        None.
        
        """
        if state == 2:
            if sender.objectName() == "log_data":
                print("Logger Enabled")
                self.generation_params["logger_active"] = True
                print(self.generation_params["logger_active"])
            elif sender.objectName() == "real_dataset":
                self.datasets_available = Utils.contains_files("./Resources/Datasets") 
                if self.datasets_available:
                    self.file = Utils.get_smallest_file("./Resources/Datasets/")
                    print("Real data Enabled")
                    self.fileButton.setEnabled(True)
                    self.fileButton.setText(f'{self.file}')
                    print("File:", self.file)
                    self.update_seasonality_widgets(True)
                else:
                    print("No data available")
                    self.fileButton.setEnabled(False)
                    self.fileButton.setText("No data available")
                    self.update_seasonality_widgets(False)
            else:
                print("Reset Analysts Info")
                self.generation_params["reset_analysts_data"] = True
                print(self.generation_params["reset_analysts_data"])                
        else:
            if sender.objectName() == "log_data":
                print("Logger Disabled")
                self.generation_params["logger_active"] = False
                print(self.generation_params["logger_active"])
            elif sender.objectName() == "real_dataset":
                self.file = "No real data!"
                print("Real data Disabled")
                self.fileButton.setEnabled(False)
                if self.datasets_available:
                    self.fileButton.setText("No dataset loaded")
                else:
                    self.fileButton.setText("No data available")
                self.update_seasonality_widgets(False)
            else:
                print("Analysts Info not changed")
                self.generation_params["reset_analysts_data"] = False
                print(self.generation_params["reset_analysts_data"])
    
    def pick_family_method(self, d):
        """
        Uses default or customized families.

        Parameters
        ----------
        d : QRadioButton
            Family distribution button.

        Returns
        -------
        None.

        """
        if d.isChecked():
            print("Default Families actived!")
            self.distribution_groupbox.setEnabled(False)
            self.generation_params["use_default_family"] = True
            self.generation_params["default_alert_pool"] = Configurator.read_configuration_section("Cybersecurity", "families")
        else:
            print("Default Families not actived!")
            self.distribution_groupbox.setEnabled(True)
            self.generation_params["use_default_family"] = False
            self.generation_params["default_alert_pool"] = {}
        self.pick_distribution_method(self.family_distribution_normal)
    
    def pick_IP_address(self, i):
        """
        Gets the type of IP address.        

        Parameters
        ----------
        i : int
            IP address index.

        Returns
        -------
        None.

        """
        self.generation_params["ip_selected_idx"] = i
        print("Variables ip selected:", str(self.ip_type.currentText()))  
    
    def update_ticket_dates(self, stage):
        """
        Updates the start and end datetimes for the generation.

        Parameters
        ----------
        stage : str
            Start or end datetime selected.

        Returns
        -------
        None.

        """    
        if stage == "initial datetime":
            self.generation_params["start_date"] = self.date_init_input.text()
            print("New initial datetime:", self.generation_params["start_date"])
        elif stage == "end datetime":
            self.generation_params["end_date"] = self.date_end_input.text()   
            print("New end datetime:", self.generation_params["end_date"])
    
    def pick_time_method(self):
        """
        Changes the time probability of the families.      

        Returns
        -------
        None.

        """
	
        if self.isChecked():
            print("In terms of time, all Families have the same probability")
            self.generation_params["time_equal_probabilities"] = True
            self.spin_time_day_light.setEnabled(False)
            self.spin_time_night_light.setEnabled(False)
        else:
            print("Families will have different probabilities during the time of the day")
            self.generation_params["time_equal_probabilities"] = False
            self.spin_time_day_light.setEnabled(True)
            self.spin_time_night_light.setEnabled(True)
                
    def pick_week_method(self):
        """
        Changes the week probability of the families.

        Returns
        -------
        None.

        """
        if self.week_equal.isChecked():
            print("In terms of the day, all Families have the same probability")
            self.generation_params["week_equal_probabilities"] = True
            self.spin_weekend.setEnabled(False)
            self.spin_week.setEnabled(False)
        else:
            print("Families will have different probabilities during the week")
            self.generation_params["week_equal_probabilities"] = False
            self.spin_weekend.setEnabled(True)
            self.spin_week.setEnabled(True)
            
    def update_families_time_probabilities(self, label, prob):
        """
        Updates the families time probabilities (daylight and night time).

        Parameters
        ----------
        label : Qlabel
            Daylight or night time labels.
        prob : float
            Probability selected for the chosen label.

        Returns
        -------
        None.
        
        """
        if label.text() == "Higher on Daylight":
            #print("Time prob:", prob.value())
            time_light_prob = float (prob.value()/3)
            #print("Time Day prob:", time_light_prob)
            self.generation_params["family_time_4h"][2]['prob'] = time_light_prob
            self.generation_params["family_time_4h"][3]['prob'] = time_light_prob
            self.generation_params["family_time_4h"][4]['prob'] = time_light_prob
              
            time_night_prob = 1 - prob.value()
            #print("Time night prob:", time_night_prob)
            time_night_day_prob = float (time_night_prob/3)
            #print("Time night day prob:", time_night_day_prob)
            self.generation_params["family_time_4h"][0]['prob'] = time_night_day_prob
            self.generation_params["family_time_4h"][1]['prob'] = time_night_day_prob
            self.generation_params["family_time_4h"][5]['prob'] = time_night_day_prob
            self.spin_time_night_light.setValue(time_night_prob)
      
        else:
            #print("Time night prob:", prob.value())
            time_night_day_prob = float (prob.value()/3)
            #print("Time night day prob:", time_night_day_prob)
            self.generation_params["family_time_4h"][0]['prob'] = time_night_day_prob
            self.generation_params["family_time_4h"][1]['prob'] = time_night_day_prob
            self.generation_params["family_time_4h"][5]['prob'] = time_night_day_prob
            
            time_light_prob = 1 - prob.value()
            #print("Time day prob:", time_light_prob)
            time_light_day_prob = float (time_light_prob/3)
            #print("Time light day prob:", time_light_day_prob)
            self.generation_params["family_time_4h"][2]['prob'] = time_light_day_prob
            self.generation_params["family_time_4h"][3]['prob'] = time_light_day_prob
            self.generation_params["family_time_4h"][4]['prob'] = time_light_day_prob
            self.spin_time_day_light.setValue(time_light_prob)
         
    def update_families_week_probabilities(self, label, prob):
        """
        Updates the families week probabilities (weekday and weekend).

        Parameters
        ----------
        label : QLabel
            Weekday or weekend labels.
        prob : float
            Probability selected for the chosen label.

        Returns
        -------
        None.

        """
        if label.text() == "Higher on Weekdays":
            #print("Week prob:", prob.value())
            week_day_prob = float (prob.value()/5)
            #print("Week Day prob:", week_day_prob)
            self.generation_params["week_time"][0]['prob'] = week_day_prob
            self.generation_params["week_time"][1]['prob'] = week_day_prob
            self.generation_params["week_time"][2]['prob'] = week_day_prob
            self.generation_params["week_time"][3]['prob'] = week_day_prob
            self.generation_params["week_time"][4]['prob'] = week_day_prob
              
            weekend_prob = 1 - prob.value()
            #print("Weekend prob:", weekend_prob)
            weekend_day_prob = float (weekend_prob/2)
            #print("Weekend Day prob:", weekend_day_prob)
            self.generation_params["week_time"][5]['prob'] = weekend_day_prob
            self.generation_params["week_time"][6]['prob'] = weekend_day_prob
            self.spin_weekend.setValue(weekend_prob)
        else:
            #print("Weekend prob:", prob.value())
            weekend_day_prob = float (prob.value()/2)
            #print("Weekend Day prob:", weekend_day_prob)
            self.generation_params["week_time"][5]['prob'] = weekend_day_prob
            self.generation_params["week_time"][6]['prob'] = weekend_day_prob
            
            week_day = 1 - prob.value()
            #print("Week prob:", week_day)
            week_day_prob = float (week_day/5)
            #print("Week Day prob:", week_day_prob)
            self.generation_params["week_time"][0]['prob'] = week_day_prob
            self.generation_params["week_time"][1]['prob'] = week_day_prob
            self.generation_params["week_time"][2]['prob'] = week_day_prob
            self.generation_params["week_time"][3]['prob'] = week_day_prob
            self.generation_params["week_time"][4]['prob'] = week_day_prob
            self.spin_week.setValue(week_day)
                
    def update_inputs(self, mode):
        """
        Updates various attributes regarding tickets, families, techniques, and other features.

        Parameters
        ----------
        mode : str
            Standard or Custom.

        Returns
        -------
        None.

        """
        if mode == "Configuration File":
            self.ticket_number.setText(str(self.generation_params['n_tickets']))
            self.family_number.setText(str(self.generation_params['families_number']))
            self.min_subfamily_number.setText(str(self.generation_params['minsubfamilies_number']))
            self.max_subfamily_number.setText(str(self.generation_params['maxsubfamilies_number']))
            self.technique_number.setText(str(self.generation_params['techniques_number']))
            self.min_subtechnique_number.setText(str(self.generation_params['minsubtechniques_number']))
            self.max_subtechnique_number.setText(str(self.generation_params['maxsubtechniques_number']))
            self.min_counter_number.setText(str(self.treatment_params['min_learning_counter']))
            self.max_counter_number.setText(str(self.treatment_params['max_learning_counter']))
        else:
            self.ticket_number.setText("")
            self.family_number.setText("")
            self.min_subfamily_number.setText("")
            self.max_subfamily_number.setText("")
            self.technique_number.setText("")
            self.min_subtechnique_number.setText("")
            self.max_subtechnique_number.setText("")
            self.min_counter_number.setText("")
            self.max_counter_number.setText("")
           
    def pick_generation_method(self):
        """
        Changes the generation mode (standard and custom).

        Returns
        -------
        None.

        """
        radioButton = self.sender()
        if radioButton.text() == "Configuration File":
            if radioButton.isChecked() == True:
                print("Standard Mode was activated!")
                self.ticketTab.setEnabled(False)
                self.familyTab.setEnabled(False)
                self.techniquesTab.setEnabled(False)
                self.learningTab.setEnabled(False)
                self.teams_configs.setEnabled(False)
                self.generate_button.setEnabled(True)
                self.generate_button.setProperty('ready', True)
                self.generate_button.setStyle(self.generate_button.style())
                self.family_season_toggle.setEnabled(True)
                self.family_season_toggle.setChecked(True) 
                self.ticket_season_toggle.setEnabled(True)
                self.interface_params["generation_mode"] = "standard"
                if not self.datasets_available:
                    self.update_seasonality_widgets(False)
                else:
                    if self.real_data_box.isChecked():
                        self.update_seasonality_widgets(True)
        if radioButton.text() == "Custom":
            if radioButton.isChecked() == True:
                print("Custom Mode activated!")
                self.ticketTab.setEnabled(True)
                self.familyTab.setEnabled(True)  
                self.techniquesTab.setEnabled(True) 
                self.learningTab.setEnabled(True) 
                self.teams_configs.setEnabled(True)
                self.generate_button.setEnabled(False)
                self.generate_button.setProperty('ready', False)        
                self.generate_button.setStyle(self.generate_button.style())
                self.family_season_toggle.setEnabled(False)
                self.family_season_toggle.setChecked(False) 
                self.ticket_season_toggle.setChecked(False)
                self.ticket_season_toggle.setEnabled(False)
                if not self.datasets_available:
                    self.update_seasonality_widgets(False)
                else:
                    if self.real_data_box.isChecked():
                        self.update_seasonality_widgets(True)
                self.interface_params["generation_mode"] = "custom"
                
        self.update_inputs(radioButton.text())
        
    def print_plots(self):
        """
        Enables ploting regarding ticket generation and treatment.

        Returns
        -------
        None.

        """
        if self.plot_toggle.isChecked():
            print("Print the families plots!")
            self.generation_params["print_plots"] = True
        else:
            print("Not printing the families plot!")
            self.generation_params["print_plots"] = False
        
    def pick_debug_method(self):
        """
        Enables the debug mode.

        Returns
        -------
        None.

        """
        if self.debug_toggle.isChecked():
            print("Debug Mode was activated!")
            self.generation_params["debug"] = True	
        else:
            print("Debug Mode not activated!")
            self.generation_params["debug"] = False
            
    def pick_ticket_seasonality(self, s):
        """
        Enables ticket seasonality from real data.

        Returns
        -------
        None.

        """
        if self.ticket_season_toggle.isChecked():
            print("Ticket Seasonality considered!")
            self.generation_params["ticket_seasonality_selector"] = True	
        else:
            print("Ticket Seasonality excluded!")
            self.generation_params["ticket_seasonality_selector"] = False
            
    def pick_ticket_growth(self):
        """
        Enables ticket growth.

        Returns
        -------
        None.

        """
        if self.ticket_growth_toggle.isChecked():
            print("Ticket growth activated!")
            self.generation_params["ticket_growth_selector"] = True	
            self.ticket_growth_doublespin.setEnabled(True)
        else:
            print("Ticket growth excluded!")
            self.generation_params["ticket_growth_selector"] = False
            self.ticket_growth_doublespin.setEnabled(False)
            
    def update_growth_rate(self):
        """
        Updates ticket growth rate.

        Returns
        -------
        None.

        """
        print("Ticket growth rate:", round(self.ticket_growth_doublespin.value(), 2))
        self.generation_params["ticket_growth_rate"] = round(self.ticket_growth_doublespin.value(), 2) 
            
    def pick_escalation_method(self, escalation_widget):
        """
        Enables and updates escalation probability.

        Parameters
        ----------
        escalation_widget : QWidget
            Escalation widget.

        Returns
        -------
        None.

        """
	
        if self.ticket_escalation_toggle.isChecked():
            print("Ticket Escalation enabled!")
            self.generation_params["ticket_escalation_selector"] = True	
            escalation_widget.setEnabled(True)
            self.escalation_slider.setValue(self.generation_params["escalate_rate_percentage"])
            self.escalation_rate_label.setText(f"Rate: {self.generation_params['escalate_rate_percentage']}%")
        else:
            print("Ticket Escalation disabled!")
            self.generation_params["ticket_escalation_selector"] = False
            escalation_widget.setEnabled(False)
            self.escalation_slider.setValue(0)
            self.escalation_rate_label.setText(f"Rate: {0}%")
                
    def pick_family_seasonality(self):
        """
        Updates familiy seasonality for the generation.

        Returns
        -------
        None.

        """
        if self.family_season_toggle.isChecked():
            print("Family Seasonality considered!")
            self.generation_params["family_seasonality_selector"] = True	
        else:
            print("Family Seasonality excluded!")
            self.generation_params["family_seasonality_selector"] = False
                    
    def update_techniques_seasonality(self):
        """
        Enables/disables technique seasonality for the generation.

        Returns
        -------
        None.

        """
        if self.duration_season_toggle.isChecked():
            print("Techniques Seasonality enabled!")
            self.generation_params["techniques_seasonality_selector"] = True	
            self.min_subtechnique_slider.setEnabled(False)
            self.min_subtechnique_cost_slider.setEnabled(False)
            self.max_subtechnique_slider.setEnabled(False)
            self.max_subtechnique_cost_slider.setEnabled(False)
        else:
            print("Techniques Seasonality disabled!")
            self.generation_params["techniques_seasonality_selector"] = True	
            self.min_subtechnique_slider.setEnabled(True)
            self.min_subtechnique_cost_slider.setEnabled(True)
            self.max_subtechnique_slider.setEnabled(True)
            self.max_subtechnique_cost_slider.setEnabled(True)
                    
    def pick_ticket_similarity(self):
        """
        Enables ticket similarity.

        Returns
        -------
        None.

        """
        if self.similar_tickets_toggle.isChecked():
            print("Ticket similarity disabled!")
            self.treatment_params["ticket_similarity_selector"] = True	
            self.coordinated_attacks_groupbox.setEnabled(True)
        else:
            print("Ticket similarity enabled!")
            self.treatment_params["ticket_similarity_selector"] = False
            self.coordinated_attacks_groupbox.setEnabled(False)
                    
    def pick_ticket_verification_method(self):
        """
        Enables ticket verification between operator and subfamily actions.

        Returns
        -------
        None.

        """
        if self.verify_tickets_toggle.isChecked():
            print("Ticket verification disabled!")
            self.treatment_params["ticket_verification_selector"] = True	
        else:
            print("Ticket similarity enabled!")
            self.treatment_params["ticket_verification_selector"] = False
               
    def pick_ip(self):
        """
        Enables IP customization.

        Returns
        -------
        None.

        """
        if self.ip_toggle.isChecked():
            print("IP included!")
            self.generation_params["ip_selector"] = True	
            self.ip_groupbox.setEnabled(True)
        else:
            print("IP excluded!")
            self.generation_params["ip_selector"] = False
            self.ip_groupbox.setEnabled(False)
            
    def pick_suspicious_method(self):
        """
        Enables behaviour tracking in suspicious countries.

        Returns
        -------
        None.

        """
        if self.track_behaviour_toggle.isChecked():
            print("Track suspicious behaviours enabled!")
            self.interface_params["suspicious_selector"] = True	
            self.sus_countries_groupbox.setEnabled(True)
        else:
            print("Track suspicious behaviours disabled!")
            self.interface_params["suspicious_selector"] = False
            self.sus_countries_groupbox.setEnabled(False)
             
    def pick_outlier_method(self):
        """
        Enables outliers for ticket generation.

        Returns
        -------
        None.

        """
        if self.outlier_toggle.isChecked():
            print("Outliers included!")
            self.interface_params["outlier_selector"] = True	
            self.outlier_groupbox.setEnabled(True)
        else:
            print("Outliers excluded!")
            self.interface_params["outlier_selector"] = False
            self.outlier_groupbox.setEnabled(False)
    
    def update_escalation_rate(self):
        """
        Updates the escalation frequency.

        Returns
        -------
        None.

        """
        self.escalation_rate_label.setText(f"Rate: {self.escalation_slider.value()}%")
        self.generation_params["escalate_rate_percentage"] = self.escalation_slider.value()
        print("Escalation rate:", self.escalation_rate_label.text())
        
    def update_subtechnique_rate(self, slider, label):
        """
        Updates the subtechnique rate duration.

        Parameters
        ----------
        slider : QSlider
            Slider for probability management.
        label : QLabel
            Label of the selected probability.

        Returns
        -------
        None.

        """
        label.setText(f"Rate: {slider.value()}%")
        
        if label.objectName() == "min_sub":
            self.generation_params["min_subtechnique_rate"] = slider.value()
            self.max_subtechnique_slider.setMinimum(slider.value() + 1)
        else:
            self.generation_params["max_subtechnique_rate"] = slider.value()
            self.min_subtechnique_slider.setMaximum(slider.value() - 1)
            
    def update_subtechnique_cost(self, slider, label):
        """
        Updates the subtechnique cost.

        Parameters
        ----------
        slider : QSlider
            Slider for cost management.
        label : QLabel
            Label of the selected cost.

        Returns
        -------
        None.

        """
        label.setText(f"Cost: {slider.value()}")
        
        if label.objectName() == "min_sub_cost":
            self.generation_params["min_subtechnique_cost"] = slider.value()
            self.generation_params["max_subtechnique_cost"] = slider.value()
        
    def update_detection_timerange(self, slider, label):
        """
        Updates detection time range.

        Parameters
        ----------
        slider : QSlider
            Slider for detection range management.
        label : QLabel
            Label of the selected timerange.

        Returns
        -------
        None.

        """
        label.setText(f"{slider.value()} minutes")
        
        if label.objectName() == "min_time_detection":
            self.generation_params["min_coordinated_attack_minutes"] = slider.value()
        else:
            self.generation_params["max_coordinated_attack_minutes"] = slider.value()
        
    def update_outlier_rate(self):
        """
        Updates the outlier frequency.

        Returns
        -------
        None.

        """
        self.outlier_rate_output.setText(f"Frequency Rate: {self.outlier_slider.value()}%")
        self.generation_params["outlier_rate"] = self.outlier_slider.value()
          
    def update_outlier_value(self, val):
        """
        Updates the outlier impact.

        Parameters
        ----------
        val : float
            Value of outlier cost.

        Returns
        -------
        None.

        """
        print("Outlier Percentage:", val)
        self.generation_params["outlier_cost"] = val
        
    def update_country_subfamily(self, value):
        """
        Updates the rate of the appearance of suspicious subfamilies.

        Parameters
        ----------
        value : float
            Probability of a subfamily being suspicious.

        Returns
        -------
        None.

        """
        print("Suspicious Subfamilies Percentage:", round(value, 2))
        self.generation_params["suspicious_subfamily"] = round(value, 2)
        
    # Verifies if the input meet certain conditions
    def check_input(self, widget):
        """
        Check if the input is valid.

        Parameters
        ----------
        widget : QLineEdit
            Widget with the parameter to be assessed.

        Returns
        -------
        None.

        """
        if widget.objectName() == "n_tickets":
            if widget.text():
                n_tickets = int(self.ticket_number.text())
                if n_tickets < 1:
                    widget.setText("")
                    InterfaceUtils.pop_message("Error", "The number of tickets must be greater than 0!")
                    return
                else:
                   self.generation_params['n_tickets'] = n_tickets

        elif widget.objectName() == "family_number":
            if widget.text():
                families = int(self.family_number.text())
                if not (1 <= families <= len(string.ascii_uppercase)):
                    widget.setText("")
                    self.selectable_families_combo.setEnabled(False)
                    print("stop")
                    InterfaceUtils.pop_message("Error", f'Valid range of the number of families is 1-{len(string.ascii_uppercase)}')
                    return
                else:
                    self.selectable_families_combo.limit = int(self.family_number.text())
                    self.selectable_families_combo.reset_items()
                    self.selected_families.setText("Random")
                    self.selectable_families_combo.setEnabled(True)
                    self.generation_params['families_number'] = families
                
                if self.datasets_available and self.generation_params["family_seasonality"] != None:
                    n_families = len(self.generation_params["family_seasonality"]["January"].keys())
                    print("Number of families in real data:", n_families)
                else:
                    n_families = len(self.generation_params["default_alert_pool"].keys())
                    print("Number of families allowed:", n_families)
                
                if int(self.family_number.text()) <= n_families and self.datasets_available:
                    print("The number of families is less or equal to real families!")
                    self.family_season_toggle.setEnabled(True)
                    self.family_season_toggle.setChecked(True)
                    self.generation_params["family_seasonality_selector"] = True
                else:        
                    print("Family Seasonality excluded! Number of families is greater than the number of families in real data.")
                    self.family_season_toggle.setEnabled(False)
                    self.family_season_toggle.setChecked(False)
                    self.generation_params["family_seasonality_selector"] = False
                
        elif widget.objectName() == "minimum_subFamilies":
            if widget.text():
                min_subfamilies = int(self.min_subfamily_number.text())
                if not (1 <= min_subfamilies <= 4):
                    widget.setText("")
                    InterfaceUtils.pop_message("Error", "Valid range of the minimum number of subfamilies is 1-4")
                    return
                else:
                    self.generation_params['minsubfamilies_number'] = min_subfamilies
                
        elif widget.objectName() == "maximum_subFamilies":
            if widget.text():
                max_subfamilies = int(self.max_subfamily_number.text())
                if not (5 <= max_subfamilies <= 11):
                    widget.setText("")
                    InterfaceUtils.pop_message("Error", "Valid range of the maximum number of subfamilies is 5-11")
                    return
                else:
                    self.generation_params['maxsubfamilies_number'] = max_subfamilies
    
        elif widget.objectName() == "minimum_attack_occurences":
            if widget.text():
                min_attacks = int(self.min_occurences_number.text())
                if not (1 <= min_attacks <= 3):
                    widget.setText("")
                    InterfaceUtils.pop_message("Error", "Valid range of the minimum attack occurences of the subfamilies is 1-3")
                    return
                else:
                    self.generation_params['min_coordinated_attack'] = min_attacks
                
        elif widget.objectName() == "maximum_attack_occurences":
            if widget.text():
                max_attacks = int(self.max_occurences_number.text())
                if not (4 <= max_attacks <= 10):
                    widget.setText("")
                    InterfaceUtils.pop_message("Error", "Valid range of the maximjm attack occurences of the subfamilies is 4-10")
                    return
                else:
                    self.generation_params['max_coordinated_attack'] = max_attacks
                
        elif widget.objectName() == "techniques_number":
            if widget.text():
                techniques = int(self.technique_number.text())
                if not (1 <= techniques <= 62):
                    widget.setText("")
                    InterfaceUtils.pop_message("Error", "Valid range of the number of techniques is 1-62")
                    self.min_subtechnique_number.setEnabled(False)
                    self.max_subtechnique_number.setEnabled(False)
                    return
                else:
                    self.generation_params['techniques_number'] = techniques
                    self.min_subtechnique_number.setEnabled(True)
                    self.max_subtechnique_number.setEnabled(True)
            else:
                self.min_subtechnique_number.setEnabled(False)
                self.max_subtechnique_number.setEnabled(False)
                    
        elif widget.objectName() == "min_subtechnique":
            if widget.text():
                techniques = int(self.technique_number.text())
                min_subtechniques = int(self.min_subtechnique_number.text())
                if not (3 <= min_subtechniques <= (255//techniques)):
                    widget.setText("")
                    InterfaceUtils.pop_message("Error", f'Valid range of the number of minimum subtechniques is 3-{255//techniques}. Two subtechniques are the initial and final steps')
                    return
                else:
                    self.generation_params['minsubtechniques_number'] = min_subtechniques
                
        elif widget.objectName() == "max_subtechnique":
            if widget.text():
                techniques = int(self.technique_number.text())
                min_subtechniques = int(self.min_subtechnique_number.text())
                max_subtechniques = int(self.max_subtechnique_number.text())
                if not (min_subtechniques <= max_subtechniques <= ((255//techniques) + min_subtechniques)):
                    widget.setText("")
                    InterfaceUtils.pop_message("Error", f'Valid range of the maximum number of subtechniques is: {min_subtechniques}-{((255//techniques) - min_subtechniques)}')
                    return
                else:
                    self.generation_params['maxsubtechniques_number'] = max_subtechniques
                
        elif widget.objectName() == "min_counter":
            if widget.text():
                min_counter = int(self.min_counter_number.text())
                if self.max_counter_number.text() != "":
                    max_counter = int(self.max_counter_number.text())
                    if min_counter > max_counter:
                        widget.setText("")
                        InterfaceUtils.pop_message("Error", "Min counter must be less than max counter")
                        return
                if min_counter == 0:
                    widget.setText("")
                    InterfaceUtils.pop_message("Error", "Min counter cannot be 0")
                    return
                else:
                    self.treatment_params['min_learning_counter'] = min_counter
                
        elif widget.objectName() == "max_counter":
            if widget.text():
                max_counter = int(self.max_counter_number.text())
                if self.min_counter_number.text() != "":
                    min_counter = int(self.min_counter_number.text())
                    if min_counter > max_counter:
                        widget.setText("")
                        InterfaceUtils.pop_message("Error", "Max counter must be greater than min counter")
                        return
                if min_counter == 0:
                    widget.setText("")
                    InterfaceUtils.pop_message("Error", "Max counter cannot be 0")
                    return
                else:
                    self.treatment_params['max_learning_counter'] = max_counter
                
        # IF all are complete turn the button to green
        if self.ticket_number.text() and self.family_number.text() and self.min_subfamily_number.text() and self.max_subfamily_number.text() and self.technique_number.text() and self.min_subtechnique_number.text() and self.max_subtechnique_number.text() and self.min_counter_number.text() and self.max_counter_number.text():
            self.generate_button.setProperty('ready', True)
            self.generate_button.setStyle(self.generate_button.style())
            self.generate_button.setEnabled(True)

    def update_analyst_same_subfamily_action_prob(self, val):
        """
        Updates probability of using the subfamily action.

        Parameters
        ----------
        val : float
            Likelihood of using the subfamily action.

        Returns
        -------
        None.

        """
        print("The probability of using the subfamily action was changed to:", round(val, 2))
        self.treatment_params["analyst_subfamily_action_probability"] = val
        
    def update_analyst_same_action_prob(self, val):
        """
        Updates probability of using the same action.

        Parameters
        ----------
        val : float
            Likelihood of using the same action.

        Returns
        -------
        None.

        """
        print("The probability of using the same action was changed to:", round(val, 2))
        self.treatment_params["analyst_same_action_probability"] = val
            
    def check_generation(self):
        """
        Generates the dataset according to the mode selected.

        Returns
        -------
        None.
        
        """
        if self.generation_custom.isChecked():
            print("Number of tickets: ", self.ticket_number.text())
            print("Number of Families: ", self.family_number.text())
            print("Types of Families: ", self.selected_families.text())
            print("Minimum number of Families: ", self.min_subfamily_number.text())
            print("Maximum number of Families: ", self.max_subfamily_number.text())
            print("Number of Techniques: ", self.technique_number.text())
            print("Minimum number of sub techniques: ", self.min_subtechnique_number.text())
            print("Maximum number of sub techniques: ", self.max_subtechnique_number.text())
        else:
            self.generation_params["default_alert_pool"] = Configurator.read_configuration_section("Cybersecurity", "families")
        self.call_generator("Cybersecurity", self.generation_params, self.treatment_params, self.countries_list, self.auxiliar_dataset_params, self.cpu_times_before, self.cpu_usage_before)
          
    def reset_generator_button(self):
        """
        Resumes the generation button after outputing the dataset.

        Returns
        -------
        None.

        """
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate")
        self.progress_report.setText("")
            
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
        # When the window is closed, stop the thread gracefullys
        for i in self.subwindows:
            i.close()
            
        if hasattr(self, "generator"):
            print("Generator thread will be closed!")
            self.generator.canceled = True
        else:
            print("No threads running")
    
        event.accept()
        print("Application closed successfully!\n")
        
    def on_success(self):
        """
        Prints generator's success message.

        Returns
        -------
        None.

        """
        print("Generation Complete!")
        
    def call_generator(self, domain, generation_params, treatment_params, countries, output_params, start_cpu, cpu_usage_before):
        """
        Calls the Generator Class to build the dataset in a thread.

        Parameters
        ----------
        domain : str
            Domain selected (cybersecurity).
        generation_params : dict
            Comprises all data about parameters related to ticket generation.
        treatment_params : dict
            Comprises all data about parameters related to ticket treatment.
        countries : dict
            Comprises information about the countries collected from an external file.
        output_params : dict
            Comprises the column features that should be included in the generated datasets.
        start_cpu : scpustimes
            Comprises information about CPU time statistics.
        cpu_usage_before : float
            Percentage of total CPU time.

        Returns
        -------
        None.

        """
        self.thread_pool = QThreadPool.globalInstance()
        self.generator = Generator(domain, generation_params, treatment_params, countries, output_params, start_cpu, cpu_usage_before)
        self.generator.signals.finished.connect(self.on_success)
        self.generator.signals.finished.connect(self.reset_generator_button)  
        self.thread_pool.start(self.generator)

        # Final resets
        self.generate_button.setText("Generating...")
        self.generate_button.setEnabled(False)
        
    def load_real_dataset(self):
        """
        Loads information from a dataset.

        Returns
        -------
        None.

        """
        self.fileButton.setEnabled(False)
        path = "./Resources/Datasets"
        self.file = Configurator.load_configuration_data(self, path)
        print("Filename:",  self.file)
        
        if self.file != "":            
            filename, file_extension = os.path.splitext(self.file)
            if file_extension == '.csv' or file_extension == '.xlsx':
                self.file = os.path.basename(self.file)
                print("File:", self.file)
                self.fileButton.setText(self.file)
                self.generation_params["ticket_seasonality"], self.generation_params["family_seasonality"], self.generation_params["family_mean_duration"], self.generation_params["family_mapping"], self.generation_params["real_family_probs"], self.generation_params["real_dataset"] = Configurator.get_ticket_seasonality(self.file, False, None, False)
                self.generation_params["ticket_seasonality_selector"], self.generation_params["family_seasonality_selector"], self.generation_params["techniques_seasonality_selector"] = True, True, False    
                self.family_season_toggle.setEnabled(True)
                self.family_season_toggle.setChecked(True) 
                self.ticket_season_toggle.setEnabled(True)
                self.ticket_season_toggle.setChecked(True)
                print("Real Dataset loaded successfully!")
            else:
                InterfaceUtils.pop_message("Real Dataset Load", "The file chosen must be an valid dataset (csv or xlsx)!")
                print("The file loaded is invalid.")
        else:
            print("Operation Canceled")
            
        self.fileButton.setEnabled(True)
        
    def update_seasonality_widgets(self, is_real_data_available):
        """
        Updates seasonality widgets based on the presence of real data.

        Parameters
        ----------
        is_real_data_available : bool
            If there is real data involved or not.

        Returns
        -------
        None.

        """
        if is_real_data_available:
            if self.generation_params["family_mapping"] == None and self.file == "no real data!":
                self.file = Utils.get_smallest_file("./Resources/Datasets/")
                self.generation_params["ticket_seasonality"], self.generation_params["family_seasonality"], self.generation_params["family_mean_duration"], self.generation_params["family_mapping"], self.generation_params["real_family_probs"], self.generation_params["real_dataset"] = Configurator.get_ticket_seasonality(self.file, False, None, False)
                self.generation_params["ticket_seasonality_selector"], self.generation_params["family_seasonality_selector"], self.generation_params["techniques_seasonality_selector"] = True, True, False    
                self.family_season_toggle.setEnabled(True)
                self.family_season_toggle.setChecked(True) 
                self.ticket_season_toggle.setEnabled(True)
                self.ticket_season_toggle.setChecked(True)
        else:
            self.generation_params["ticket_seasonality_selector"], self.generation_params["family_seasonality_selector"], self.generation_params["techniques_seasonality_selector"] = False, False, False    
            self.generation_params["ticket_seasonality"], self.generation_params["family_seasonality"], self.generation_params["family_mean_duration"], self.generation_params["family_mapping"], self.generation_params["real_family_probs"], self.generation_params["real_dataset"] = None, None, None, None, None, None
            self.family_season_toggle.setEnabled(False)
            self.family_season_toggle.setChecked(False) 
            self.ticket_season_toggle.setEnabled(False)
            self.ticket_season_toggle.setChecked(False)
               
def call_application():
    """
    Initiates SNOOKER's application

    Returns
    -------
    None.

    """
    print("\014")
    os.chdir("../../")

    cpu_times_before = psutil.cpu_times()
    cpu_usage_before = psutil.Process().cpu_percent()
    print(f'Initial memory usage: {psutil.Process().memory_info().rss  / (1024 * 1024)}')
    
    app = QtCore.QCoreApplication.instance()
    myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    if app is None:
        app = QApplication(sys.argv)
        
    win = SNOOKER(cpu_times_before, cpu_usage_before)

    qr = win.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    win.move(qr.topLeft()) 
    win.move(win.pos().x(), win.pos().y() - 200)

    win.show()
    sys.exit(app.exec())

call_application()