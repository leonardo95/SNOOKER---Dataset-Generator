"""
Created on Mon Sep  7 15:38:12 2020

@author: Leonado Ferreira
@goal: Main class of the project where the tickets are created and handled by the operators
"""

from Code.Utils import Utils, UtilsParams, BufferedRandomChoiceGenerator
from Code.Configurator import Configurator

import pandas as pd
from collections import OrderedDict
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import string, random, sys, pytz, calendar
from memory_profiler import profile
from scipy.special import kl_div
from scipy import stats

class DistributionData:
    def __init__(self, ticket_seasonality_selector, ticket_seasonality, fam_seasonality_selector, fam_seasonality, day_time, week_time, day_ticket_spikes, distribution_mode, time_equal_probs, week_equal_probs):
        """
        Initiates data about incidents distribution.

        Parameters
        ----------
        ticket_seasonality_selector : bool
            Include or not the ticket seasonality of the real dataset.
        ticket_seasonality : dict
            Comprises the ticket date probabilities retrieved from the real dataset.
        fam_seasonality_selector : bool
            Include or not the family seasonality of the real dataset.
        fam_seasonality : dicy
            Comprises the monthly probabilities of the families retrieved from the real dataset.
        day_time : dict
            Comprises information about time (divided in 5 slots of 4 hours).
        week_time : dict
            Comprises information about all days of the week (probabilities).
        day_ticket_spikes: dict    
            Comprises information about potential ticket surges during the day.
        distribution_mode : str
            Follows standard or custom generation.
        time_equal_probs : bool
            Daytime can have equal or custom probability.
        week_equal_probs : bool
            Days of the week can have equal or custom probability.

        Returns
        -------
        None.

        """
        self.family_time_probability_pool, self.family_week_probability_pool, self.family_month_probability_pool = {}, {}, {}
        self.ticket_seasonality_selector = ticket_seasonality_selector
        self.ticket_seasonality = ticket_seasonality
        self.family_seasonality_selector = fam_seasonality_selector
        self.family_seasonality = fam_seasonality
        self.family_time_4h = day_time
        self.week_time = week_time
        self.day_ticket_spikes = day_ticket_spikes
        self.distribution_mode = distribution_mode
        self.time_equal_probabilities = time_equal_probs
        self.week_equal_probabilities = week_equal_probs
        
class SuspiciousData:
    def __init__(self, suspicious_countries, suspicious_subfamily, min_coordinated_attack, max_coordinated_attack, min_coordinated_attack_minutes, max_coordinated_attack_minutes, suspicious_ips):
        """
        Initiates data about suspicious activity.

        Parameters
        ----------
        suspicious_countries : dict
            Comprises data about the suspicious countries.
        suspicious_subfamily : float
            Rate of a subfamily being suspicious.
        min_coordinated_attack : int
            Minimum number of cordinated attacks (sharing client and team).
        max_coordinated_attack : int
            Maximum number of cordinated attacks (sharing client and team.
        min_coordinated_attack_minutes : int
            Minimum detection time of cordinated attacks.
        max_coordinated_attack_minutes : int
            Maximum detection time of cordinated attacks.
        suspicious_ips : dict
            Comprises information about suspicious Ips.

        Returns
        -------
        None.

        """
        self.suspicious_countries = suspicious_countries
        self.suspicious_subfamily = suspicious_subfamily
        self.min_coordinated_attack = min_coordinated_attack
        self.max_coordinated_attack = max_coordinated_attack
        self.min_coordinated_attack_minutes = min_coordinated_attack_minutes
        self.max_coordinated_attack_minutes = max_coordinated_attack_minutes
        self.suspicious_ips = suspicious_ips

class TicketGenerator:
    def __init__(self, gen_id, generation_params, logger):
        """
        Initiates essential dictionaries and other relevenat parameters for ticket generation

        Parameters
        ----------
        gen_id : str
            Unique generation identifier.
        generation_params : dict
            Comprises all data about parameters related to ticket generation.
        logger : Logger
            Logging module used for recording and debuging.

        Returns
        -------
        None.

        """
        self._id = gen_id
        self.tickets, self.clients_info, self.family_steps_pool, self.subfamily_pool = {}, {}, {}, {}
        
        self.n_tickets = generation_params["n_tickets"]
        self.ticket_growth_rate = generation_params["ticket_growth_rate"]
        self.start_date = generation_params["start_date"]
        self.end_date = generation_params["end_date"]
        self.clients_number = generation_params["clients_number"]
          
        self.family_selection = generation_params["family_selection"]
        self.use_default_family = generation_params["use_default_family"]
        self.family_number = generation_params['families_number']
        self.family_pool = generation_params["default_alert_pool"]
        self.escalate_rate_percentage = generation_params["escalate_rate_percentage"]
        self.techniques_number = generation_params["techniques_number"]
       
        self.minsubfamilies_number = generation_params['minsubfamilies_number']
        self.maxsubfamilies_number = generation_params['maxsubfamilies_number']
        self.min_subtechniques_number = generation_params['minsubtechniques_number']
        self.max_subtechniques_number = generation_params['maxsubtechniques_number']
        self.min_subtechnique_cost = generation_params["min_subtechnique_cost"]
        self.max_subtechnique_cost = generation_params["max_subtechnique_cost"]
        self.min_subtechnique_rate = generation_params["min_subtechnique_rate"]
        self.max_subtechnique_rate = generation_params["max_subtechnique_rate"]
        self.with_ip = generation_params["with_ip"]
        self.analysts_info = generation_params["analysts_skills"]
        self.ips_pool = generation_params["ips_pool"]
        self.ip_selected_idx = generation_params["ip_selected_idx"]
        self.special_steps = generation_params["special_steps"]
        
        self.family_mean_duration = generation_params["family_mean_duration"]
        
        self.techniques_seasonality_selector = generation_params["techniques_seasonality_selector"]
        self.ip_selector = generation_params["ip_selector"]
        self.ticket_escalation_selector = generation_params["ticket_escalation_selector"]
        
        self.suspicious_data = SuspiciousData(generation_params["suspicious_countries"], generation_params["suspicious_subfamily"], generation_params["min_coordinated_attack"], generation_params["max_coordinated_attack"], generation_params["min_coordinated_attack_minutes"], generation_params["max_coordinated_attack_minutes"], generation_params["suspicious_ips"])
        self.distribution_data = DistributionData(generation_params["ticket_seasonality_selector"], generation_params["ticket_seasonality"], generation_params["family_seasonality_selector"], generation_params["family_seasonality"], generation_params["family_time_4h"], generation_params["week_time"], generation_params["day_ticket_spikes"], generation_params["distribution_mode"], generation_params["time_equal_probabilities"], generation_params["week_equal_probabilities"])
        self.aux_data = UtilsParams(generation_params["outlier_rate"], generation_params["outlier_cost"], generation_params["action_operations"], generation_params["max_priority_levels"], generation_params["debug"], logger)
        
    def get_families_probabilities(self, thread_canceled, generation_params, weight, max_features):
        """
        Generates the pool of families to reduce the execution time.

        Parameters
        ----------
        thread_canceled : bool
            Thread status (cancels generation if TRUE).
        generation_params : dict
            Comprises all data about parameters related to ticket generation.
        weight : int
            Used for the interface progress bar (deprecated).
        max_features : int
            Number of max features that a family can have.

        Returns
        -------
        None.

        """
        
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "\nGet Families Probabilities")
        alert_pool = {}

        if self.family_selection == "Random" and generation_params["family_mapping"] != None:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Using Random Family Selection")
            families_selected = Utils.get_first_n_elements(generation_params["family_mapping"], self.family_number)
            print("families selected:", families_selected)
        else:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Using Customized Family Selection")
            if generation_params["family_mapping"] != None:
                families_selected = self.family_selection.split(" - ")
            else:
                families_selected = Utils.build_random_family_names(generation_params["families_number"])
                print(families_selected)

        if self.use_default_family:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Using Default families")
            for fam in families_selected:
                alert_pool[fam] = {}
                Utils.copy_dict(alert_pool[fam], self.family_pool[fam])
                if self.distribution_data.family_seasonality_selector:
                    alert_pool[fam]["real_family"] = families_selected[fam]
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'{fam} corresponds to {families_selected[fam]}')

                alert_pool[fam]["extra_features"] = []
                n_extra_features = random.randint(0, max_features)
                selected_features = random.sample(range(max_features), n_extra_features)

                for i in selected_features:
                    feature_id = f'_feature_{i}'
                    alert_pool[fam]["extra_features"].append(feature_id)
                if self.ip_selector:
                    alert_pool[fam]["ip"] = np.random.choice([True, False], p=[self.with_ip, 1-self.with_ip])
        else:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Using New Families")
            for fam in families_selected:
                if not thread_canceled:
                    if fam not in alert_pool.keys():
                        #print("Family", fam)
                        subfamily_number = random.randint(self.minsubfamilies_number, self.maxsubfamilies_number)
                        Utils.instantiate_family(alert_pool, fam, subfamily_number, max_features, self.distribution_data, self.aux_data, self.ip_selector)
                        if self.distribution_data.family_seasonality_selector:
                            alert_pool[fam]["real_family"] = families_selected[fam]

        # The families probabilities are assigned in intervals of 5 minutes
        time_slots = (60/5) * 24
        for k in alert_pool.keys():
            if not thread_canceled:
                Utils.assign_family_probabilities(k, alert_pool, time_slots, self.distribution_data)

        self.family_pool = alert_pool
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Alert pool: {alert_pool}')
        
    def get_last_appearance_time(self, curr_ticket, first_ticket):
        """
        Calculates the time difference between similar tickets (minutes).

        Parameters
        ----------
        curr_ticket : int
            Current ticket identifier.
        first_ticket : int
            First ticket identifier.

        Returns
        -------
        last_occurence : str
            Last time a similar case occurred.

        """
        last_occurence = ""
        curr_ticket_time = self.tickets[curr_ticket]['raised']
        first_ticket_time = self.tickets[first_ticket]['raised']
        time_diff = curr_ticket_time - first_ticket_time

        minutes = round(time_diff.total_seconds() / 60)
        last_occurence = f'The same problem happened {minutes} minutes ago'
        return last_occurence

    def get_clients(self, lower_bound, upper_bound, size, prefix):
        """
        Generates clients (simulate real enterprises).

        Parameters
        ----------
        lower_bound : int
            Minimum number of clients.
        upper_bound : int
            Maximum number of clients.
        size : int
            Number of clients required for the generation (same number of the tickets).
        prefix : str
            Prefix of the clients.

        Returns
        -------
        random_integers_with_strings : list
            Clients generated for all tickets.

        """
        random_integers = np.random.randint(lower_bound, upper_bound + 1, size=size)
        random_integers_with_strings = [f"{prefix}{integer}" for integer in random_integers]
        return random_integers_with_strings

    def process_step(self, team, family, step, sub_techniques_range, intermediary_techniques_dur, locked):
        """
        Generates sets of subtechniques for each technique used in the family.

        Parameters
        ----------
        team : str
            Team analyzed.
        family : str
            Family analyzed.
        step : str
            Technique analyzed.
        sub_techniques_range : int
            Number of subtechniques to be generated.
        intermediary_techniques_dur : list
            Duration of the techniques to consider in the subtechnique duration generation (can be influenced by real treatment).
        locked : list
            List of techniques that are not analyzed (special steps like initiate, end, and transfer steps were already analyzed previously).

        Returns
        -------
        None.

        """
        sub_techniques_num = random.randint(sub_techniques_range[0], sub_techniques_range[1])
        build_subtechniques = True

        if step in locked:
            if step in self.special_steps["init_opt"].keys():
                act_type = "init_opt"
            elif step in self.special_steps["end_opt"].keys():
                act_type = "end_opt"
            else:
                act_type = "transfer_opt"

            if bool(self.special_steps[act_type][step]):
                if act_type == "transfer_opt":
                    self.family_steps_pool[team][family]["transfer_opt"][step] = self.special_steps[act_type][step]
                else:
                    self.family_steps_pool[team][family][step] = self.special_steps[act_type][step]
                build_subtechniques = False
        else:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Step {step} is not locked')
            self.family_steps_pool[team][family][step] = {}

        if build_subtechniques:
            sub_techniques = []
            if self.techniques_seasonality_selector:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Intermediary step dur: {intermediary_techniques_dur[step]}')
                intermediary_subtechniques_dur = Utils.build_subtechniques_dur(intermediary_techniques_dur[step], sub_techniques_num)
            
            for i in range(sub_techniques_num):
                int_technique = random.randint(0, 255)
                # This will break for negative values -> consider[3:]
                hex_technique = hex(int_technique)[2:]
                locked_techniques_pool = sub_techniques + locked

                while str(hex_technique) in locked_techniques_pool:
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'The technique {hex_technique} already exists. Try another')
                    int_technique = random.randint(0, 255)
                    hex_technique = hex(int_technique)[2:]

                sub_techniques.append(hex_technique)

                if self.techniques_seasonality_selector:
                    step_cost = intermediary_subtechniques_dur[i]
                    self.family_steps_pool[team][family][step][hex_technique] = step_cost
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Step {step} - Subtechnique accepted {hex_technique} with dur {step_cost}')
                else:
                    step_cost = random.randint(self.min_subtechnique_cost, self.max_subtechnique_cost)
                    multiplier = random.randint(self.min_subtechnique_rate, self.max_subtechnique_rate)
                    step_multiplied = int(step_cost * multiplier/100)
                    self.family_steps_pool[team][family][step][hex_technique] = step_multiplied
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Step {step} - Multiplier: {multiplier}. Multiplier Converted: {step_multiplied}')

    def process_action(self, family, action, sub_techniques_range, intermediary_main_steps, locked_techniques):
        """
        Based on probabilities, the steps of an action (techniques) are anakyzed and the subtechniques generated.

        Parameters
        ----------
        family : str
            Family being analyzed.
        action : str
            Action to treat the specific family.
        sub_techniques_range : int
            Number of subtechniques to be generated.
        intermediary_main_steps : list
            Intermediate techniques.
        locked_techniques : list
            List of techniques that are not analyzed (special steps like initiate, end, and transfer steps were already analyzed previously).

        Returns
        -------
        None.

        """
        
        if self.techniques_seasonality_selector:
            locked_duration_steps = Utils.get_locked_techniques_duration(self.special_steps, action)
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'With techniques seasonality. lock techniques total dur: {locked_duration_steps}')

        for team in list(self.analysts_info.keys()):    
            if team not in self.family_steps_pool:
                self.family_steps_pool[team] = {}
            self.family_steps_pool[team][family] = {}
            self.family_steps_pool[team][family]["transfer_opt"] = {}
            self.family_steps_pool[team][family]["other_steps"] = {}
            intermediary_techniques_dur = []
            
            if self.techniques_seasonality_selector:
                real_family = self.family_pool[family]["real_family"]
                real_family_duration = round(self.family_mean_duration[real_family])
                if locked_duration_steps < real_family_duration:
                    real_family_duration -= locked_duration_steps
                intermediary_techniques_dur = Utils.split_actions_dur(real_family_duration, intermediary_main_steps)
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Real family: {real_family} - Mean duration: {real_family_duration}\nSubtechniques range: {sub_techniques_range}, Intermediary techniques duration: {intermediary_techniques_dur}')
            
            for step in action:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Step {step} is being analyzed')
                if step not in self.family_steps_pool[team][family].keys(): 
                    self.process_step(team, family, step, sub_techniques_range, intermediary_techniques_dur, locked_techniques)

    def build_action(self, family, length, sub_techniques_range, locked_techniques):
        """
        Generates a random action with a specific size.

        Parameters
        ----------
        family : str
            Family being analyzed.
        length : int
            Action size.
        sub_techniques_range : int
            Number of subtechniques to generated within each action step (techniques).
        locked_techniques : lits
            List of techniques that are not analyzed (special steps like initiate, end, and transfer steps were already analyzed previously).

        Returns
        -------
        action_result : str
            Action generated.

        """
        middle_actions = []
        techniques_pool = string.ascii_letters + string.digits
        init_technique_chosen = random.choice(list(self.special_steps["init_opt"].keys()))
        end_technique_chosen = random.choice(list(self.special_steps["end_opt"].keys()))

        if length > 1:
            techniques_selected = random.sample([tec for tec in techniques_pool if tec not in locked_techniques], k=(self.techniques_number-2))
        else:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Length less than 2!")
            techniques_selected = random.sample([tec for tec in string.ascii_letters if tec not in locked_techniques], k=(self.techniques_number-2))
        
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Techniques num: {self.techniques_number}, Techniques selected: {techniques_selected}. First technique: {init_technique_chosen}, End technique: {end_technique_chosen}, Length: {length}')
        action_result = str(init_technique_chosen)
        
        if length > self.techniques_number:
            middle_actions = random.choices(techniques_selected, k=(length-2))
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Repeated steps included since length is greater than the number of techniques available") 
        else:
            middle_actions = random.sample(techniques_selected, k=(length-2))

        action_result += ''.join(middle_actions)
        action_result = f'{action_result}{end_technique_chosen}'

        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'The family {family} has the action: {action_result}') 
        self.process_action(family, action_result, sub_techniques_range, middle_actions, locked_techniques)

        return action_result

    def build_family_action(self, family, sub_techniques_range, locked_techniques):
        """
        Builds an random action to treat the family.

        Parameters
        ----------
        family : str
            Family being analyzed.
        sub_techniques_range : int
            Number of subtechniques to generated within each action step (techniques).
        locked_techniques : lits
            List of techniques that are not analyzed (special steps like initiate, end, and transfer steps were already analyzed previously).

        Returns
        -------
        None.

        """
        if self.techniques_number < 10:
            # We assumed that if the number of techniques is < 10, each family should have between 3-5 techniques
            length_min = random.randint(3, 4)
            length_max = random.randint(4, 5)
        else:
            # We assumed that if the number of techniques is > 10, each family should have between 2-8 techniques
            length_min = random.randint(2, 4)
            length_max = random.randint(5, 8)

        length = random.randint(length_min, length_max)
    
        action = self.build_action(family, length, sub_techniques_range, locked_techniques)
        self.family_pool[family]["action"] = action

        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger,"Action of each family assigned") 

    def generate_actions(self, thread_canceled, weight, actions_already_built):
        """
        Action generator handler for families and subfamilies.        

        Parameters
        ----------
        thread_canceled : bool
            Thread status (cancels generation if TRUE).
        weight : int
            Used for the interface progress bar (deprecated).
        actions_already_built : bool
            Whether actions were already built or not.

        Returns
        -------
        None.

        """
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "\nGenerate actions for ticket treatment") 

        first_team = list(self.analysts_info.keys())[0]
        dataset = self.tickets[first_team]
        Utils.split_subfamilies_for_each_team(self.subfamily_pool, first_team)
            
        locked_techniques = Utils.get_locked_techniques(self.special_steps)
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Locked techniques: {locked_techniques}') 

        for i in dataset.keys():
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Ticket id: {i}') 
            subfamily = dataset[i]["subfamily"]            
            dataset[i]['team'] = self.subfamily_pool[subfamily]["assigned team"]
            if dataset[i]['team'] == "L4":
                if 'escalate' in dataset[i]:
                    dataset[i]['escalate'] = False
                    
            if actions_already_built:
                sub_techniques_range = []
                sub_techniques_range.append(self.min_subtechniques_number)
                sub_techniques_range.append(self.max_subtechniques_number)
                self.build_family_subfamily_actions(dataset[i]["family"], subfamily, sub_techniques_range, locked_techniques)

        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "All actions generated for the families and subfamilies") 

    def build_family_subfamily_actions(self, family, subfamily, sub_techniques_range, locked_techniques):
        """
        Checks if actions were already generated for families and subfamilies. If not, it generates a new action for the family or subfamily

        Parameters
        ----------
        family : str
            Family analyzed.
        subfamily : str
            Subfamily analyzed.
        sub_techniques_range : int
            Number of subtechniques to generated within each action step (techniques).
        locked_techniques : lits
            List of techniques that are not analyzed (special steps like initiate, end, and transfer steps were already analyzed previously).

        Returns
        -------
        None.

        """
        if "action" not in self.family_pool[family].keys():
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Family {family} does not have an action') 
            self.build_family_action(family, sub_techniques_range, locked_techniques)
        else:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Family {family} action already exists') 

        if subfamily in self.subfamily_pool:
            if self.subfamily_pool[subfamily]['teams_actions']:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Sub actions for teams on {subfamily} already exists')
            else:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Sub actions for teams on {subfamily} does not exist')
                Utils.build_subfamily_action_teams(self.analysts_info, family, subfamily, self.family_pool, self.family_steps_pool, self.subfamily_pool, self.aux_data)

    def get_timestamps(self, step_transitions, allocated_timestamp, outlier):
        """
        Gets the timestamps of each action step.  

        Parameters
        ----------
        step_transitions : list
            List of all steps timestamps.
        allocated_timestamp : int
            Allocated timestamp of the ticket.
        outlier : bool
            It is an outlier or not.

        Returns
        -------
        transition_dates : list
            List of transition timestamps.

        """
        transition_dates = []
        if outlier:
            step_transitions= Utils.update_step_outlier(step_transitions, self.aux_data.outlier_cost)
        
        transition_dates.append(allocated_timestamp)
        for i in step_transitions:
            allocated_timestamp= allocated_timestamp + i * 60
            transition_dates.append(allocated_timestamp)

        return transition_dates

    def output_dataset(self, thread_canceled, weight, format_idx, dataset_params, actions_similarity, shifts_data, family_mapping, show_plots, real_family_probs, real_dataset, family_subtechniques, plot_title, gen_type):        
        """
        Outputs the dataset generated.

        Parameters
        ----------
        thread_canceled : bool
            Thread status (cancels generation if TRUE).
        weight : int
            Used for the interface progress bar (deprecated).
        format_idx : int
            0 - CSV and 1 - XLSX.
        dataset_params : dict
            Comprises the column features that should be included in the generated datasets.
        actions_similarity : int
            Difference permitted between subfamily action and operator action (if greater that its value, the ticket is escalated to a more advanced team).
        shifts_data : dict
            Work shifts of the operators.
        family_mapping : dict
            Maps synthetic families with real ones.
        show_plots : bool
            Show or do not show plots about ticket and family distribution, among other features.
        real_family_probs: dict
            Comprises the probabilities of the real families.
        real_dataset : dataframe
            Real dataset.
        family_subtechniques : dict
            Information about all families analyzed by the teams during ticket treatment
        plot_title : str
            Title of the generated dataset.
        gen_type : str
            Generation with or without real data.

        Returns
        -------
        None.

        """
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Ticket Analysis")
        extra_feat = Utils.get_extra_features_used(self.family_pool)

        ticket_ids, ticket_priority, ticket_int_priority, ticket_escalate, clients= [], [], [], [], []
        similar_tickets, coord_tickets, ticket_inherited_elapsed_time= [], [], []
        locations, locations_time, location_utc_date, location_utc_timestamp= [], [], [], []
        ticket_unfixed_time, ticket_unfixed_time_timestamp, ticket_timestamps, ticket_fixed_time= [], [], [], []
        alert_family, family_actions, alert_subfamily, subfamily_actions, alert_subfamily_duration= [], [], [], [], []
        ticket_teams, ticket_teams_users, analysts_actions, analyst_actions_status, analyst_action_duration, analyst_action_duration_outlier= [], [], [], [], [], []
        analysts_available, analysts_chosen, analyst_chosen_action, analyst_action_status= [], [], [], []
        ticket_duration, ticket_status, ticket_suspicious, alert_outliers= [], [], [], []
        alert_shifted, user_shifts, = [], []
        
        ip_data_features = ["source_ip", "source_port", "destination_ip", "destination_port"]

        wait_times, resolution_times, ticket_dates = [], [], []
        tickets_summary, priorities_wait_time, dates_month_wait_time, dates_week_wait_time = {}, {}, {}, {}

        for i in self.tickets.keys():
            #print("Ticket id:", i)
            ticket= self.tickets[i]
            country= ticket['country']
            action= ticket['action']
            family= ticket['family']
            subfamily= ticket['subfamily']
            user= ticket['analyst']
            team= ticket['team']
            client= ticket['client']
            dur= ticket['duration']
            
            subfamily_dur, transitions= Utils.get_action_duration(family, self.subfamily_pool[subfamily]["teams_actions"][team], team, None, None, self.family_steps_pool, family_subtechniques, self.aux_data)

            replicated= False
            if "replicated" in ticket.keys():
                replicated= True

            ticket_ids.append(i)
            alert_family.append(family)
            family_actions.append(self.family_pool[family]["action"])
            alert_subfamily.append(subfamily)
            subfamily_actions.append(self.subfamily_pool[subfamily]["teams_actions"][team])
            ticket_teams.append(team)
            ticket_status.append(ticket["status"])
            ticket_priority.append(ticket["priority"])
            ticket_int_priority.append(self.family_pool[family]["priority"])
            analyst_chosen_action.append(action)
            location_utc_date.append(ticket['raised'])
            ticket_unfixed_time.append(ticket['allocated'])
            ticket_fixed_time.append(ticket['fixed'])
            analysts_chosen.append(user)
            analyst_action_duration.append(dur)
            analyst_action_duration_outlier.append(ticket['duration_outlier'])
            
            wait_time = Utils.calculate_timestamp_diff(ticket['raised_tsp'], ticket['allocated_tsp'], "minutes")
            if self.family_pool[family]["priority"] not in priorities_wait_time:
                priorities_wait_time[self.family_pool[family]["priority"]] = {}
            
            priorities_wait_time[self.family_pool[family]["priority"]][ticket["raised"]] = wait_time
            ticket_dates.append(ticket['raised'].date())
            
            if wait_time != 0:
                if ticket['raised'].date() not in dates_month_wait_time:
                    dates_month_wait_time[ticket['raised'].date()] = []
                dates_month_wait_time[ticket['raised'].date()].append(wait_time)

                hour_of_week = ticket['raised'].weekday() * 24 + ticket['raised'].hour
                if hour_of_week not in dates_week_wait_time:
                    dates_week_wait_time[hour_of_week] = []
                dates_week_wait_time[hour_of_week].append(wait_time)

            if "subfamily action duration" in dataset_params and dataset_params["subfamily action duration"]:
                alert_subfamily_duration.append(subfamily_dur)
            if "team analysts" in dataset_params and dataset_params["team analysts"]:
                ticket_teams_users.append(list(self.analysts_info[team]["analysts"].keys()))
            #if "analysts actions" in dataset_params and dataset_params["analysts actions"]:
            #    analysts_actions.append(str(ticket["solutions available"])[1:-1])
            if "analyst actions status" in dataset_params and dataset_params["analyst actions status"]:
                analyst_actions_status.append(ticket["solutions status"])
            if "available analysts" in dataset_params and dataset_params["available analysts"]:
                analysts_available.append(str(ticket["analysts available"])[1:-1])
            if "escalate" in dataset_params and dataset_params["escalate"]:
                ticket_escalate.append(ticket["escalate"])
            if "country" in dataset_params and dataset_params["country"]:
                locations.append(country)
            #if "country time" in dataset_params and dataset_params["country time"]:
            #    locations_time.append(ticket['local time'])
            # if "Raised (Min)" in dataset_params and dataset_params["Raised (Min)"]:
            #    locations_utc_date_minimized.append(ticket['time min'])
            if "client" in dataset_params and dataset_params["client"]:
                clients.append(client)
            if "wait time" in dataset_params and dataset_params["wait time"]:
                ticket_duration.append(wait_time)
            if "analyst shift" in dataset_params and dataset_params["analyst shift"]:
                user_shifts.append(self.analysts_info[team]["analysts"][user]["shift"])
            if "suspicious" in dataset_params and dataset_params["suspicious"]:
                ticket_suspicious.append(ticket["suspicious"])
            if "stages" in dataset_params and dataset_params["stages"]:
                ticket_timestamps.append(self.get_timestamps(ticket['steps_transitions'], ticket["allocated_tsp"], ticket['outlier']))
            if "raised_tsp" in dataset_params and dataset_params["raised_tsp"]:
                location_utc_timestamp.append(ticket["raised_tsp"])
            if "allocated_tsp" in dataset_params and dataset_params["allocated_tsp"]:
                ticket_unfixed_time_timestamp.append(ticket["allocated_tsp"])
            
            for feature in extra_feat:
                if feature in ip_data_features:
                    if feature in ticket:
                        extra_feat[feature].append(ticket[feature])
                    else:
                        extra_feat[feature].append("---")
                else:
                    if feature in ticket["extra_features"]:
                        extra_feat[feature].append(True)
                    else:
                        extra_feat[feature].append(False)

            if replicated:
                similar= f'Replicated from ticket {ticket["replicated"]}'
                similar_tickets.append(similar)
                ticket_inherited_elapsed_time.append("---")
                if "coordinated" in dataset_params and dataset_params["coordinated"]:
                    coord_tickets.append("---")
            else:
                if ticket["similar"]:
                    similar_tickets.append(ticket["similar_ids"])
                    ticket_inherited_elapsed_time.append(self.get_last_appearance_time(i, ticket["similar_ids"][-1]))
                else:
                    similar_tickets.append("---")
                    ticket_inherited_elapsed_time.append("--")
                if "coordinated" in dataset_params and dataset_params["coordinated"]:
                    if ticket["coordinated"] != "---":
                        coord_tickets.append(ticket["coordinated"])
                    else:
                        coord_tickets.append("---")

            if ticket["status"] == "Transfer":
                if ticket['escalate']:
                    if replicated:
                        analyst_action_status.append("Action updated due to ESCALATION Status")
                    else:
                        analyst_action_status.append("Last step removed due to ESCALATION Status")
                else:
                    if ticket["replication_status"] == "Verification":
                        analyst_action_status.append(f'Distance GREATER than {actions_similarity}')
                    else:
                        analyst_action_status.append("Max similarity reached")
            else:
                analyst_action_status.append(f'Distance LESS {actions_similarity}')

            if ticket['outlier']:
                alert_outliers.append(True)
            else:
                alert_outliers.append(False)
                
            if team not in tickets_summary:
                tickets_summary[team] = {}
                tickets_summary[team]["shifts"] = {}
                tickets_summary[team]["scheduled"] = {}
                tickets_summary[team]["scheduled"]["other_day"] = 0
                tickets_summary[team]["scheduled"]["other_shift"] = 0
                tickets_summary[team]["scheduled"]["others"] = 0
                
            resolution_times.append(ticket['duration_outlier'])
                
            allocated_shift = Utils.get_ticket_shift(ticket['allocated'].time(), shifts_data)    
            if allocated_shift not in tickets_summary[team]["shifts"]:
                tickets_summary[team]["shifts"][allocated_shift] = {}
                
            tickets_summary[team]["shifts"][allocated_shift][i] = {}
            tickets_summary[team]["shifts"][allocated_shift][i]["time_spent"] = dur
            tickets_summary[team]["shifts"][allocated_shift][i]["wait_time"] = wait_time

            wait_times.append(wait_time)
            tickets_summary[team]["shifts"][allocated_shift][i]["analyst"] = user
            tickets_summary[team]["shifts"][allocated_shift][i]["family"] = family
            tickets_summary[team]["shifts"][allocated_shift][i]["subfamily"] = subfamily
            
            if ticket['raised'] != ticket['allocated']:
                if ticket['raised'].day != ticket['allocated'].day:
                    tickets_summary[team]["scheduled"]["other_day"] += 1
                elif Utils.get_ticket_shift(ticket['raised'].time(), shifts_data) != Utils.get_ticket_shift(ticket['allocated'].time(), shifts_data):
                    tickets_summary[team]["scheduled"]["other_shift"] += 1
                else:
                    tickets_summary[team]["scheduled"]["others"] += 1
                
        data = {'id': ticket_ids, 'country': locations, 'country time':locations_time,    
                'raised': location_utc_date, 'raised_tsp': location_utc_timestamp,
                'allocated': ticket_unfixed_time, 'allocated_tsp': ticket_unfixed_time_timestamp, 
                'stages': ticket_timestamps, 'fixed': ticket_fixed_time, 'wait time': ticket_duration,
                'init_priority': ticket_int_priority, 'priority': ticket_priority, 'client': clients,
                'family': alert_family, 'family action': family_actions, 'subfamily': alert_subfamily, 
                'subfamily action': subfamily_actions, 'subfamily action duration': alert_subfamily_duration, 
                'team': ticket_teams, 'team analysts': ticket_teams_users, 'analysts available': analysts_available, 
                'analysts actions': analysts_actions, 'analysts actions status': analyst_actions_status,
                'analyst': analysts_chosen, 'analyst shift': user_shifts,
                'action': analyst_chosen_action, 'action status': analyst_action_status,
                'duration': analyst_action_duration, 'duration_outlier': analyst_action_duration_outlier, 'coordinated': coord_tickets, 
                'similar': similar_tickets, 'inheritance elapsed time': ticket_inherited_elapsed_time, 
                'status': ticket_status, 'escalate': ticket_escalate, 'suspicious': ticket_suspicious,
                'outlier': alert_outliers, 'shifted': alert_shifted}

            
        if gen_type == "real":
            output_path = f'Dataset_{self._id}'
        elif gen_type == "no_real":
            output_path = f'Dataset_without_real_{self._id}'
        else:
            output_path = f'Dataset_uniform_{self._id}'
        
        dataset = Utils.format_generation_datasets(data, output_path, format_idx, dataset_params, extra_feat, plot_title)
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Tickets outputted")
        
        if show_plots:
            self.plot_ticket_distribution(dataset, "daily")
            self.plot_ticket_distribution(dataset, "daily_monthly")
            self.plot_ticket_distribution(dataset, "weekly")
            self.plot_ticket_distribution(dataset, "hour")
            self.plot_ticket_distribution(dataset, "monthly")
            Utils.plot_dataset_distribution(ticket_dates)
            self.plot_families_distribution(dataset)
            Utils.plot_wait_times(ticket_duration, location_utc_date, plot_title)
            Utils.plot_wait_times_by_init_priority(priorities_wait_time)

        if real_dataset is not None:
            self.evaluate_real_synthetic_datasets(dataset, real_dataset, real_family_probs, family_mapping, show_plots)
        self.evaluate_team_performance(tickets_summary)
        self.get_tickets_statistics(tickets_summary, len(self.tickets), wait_times, resolution_times)
          
    # Plots monthly ticket distribution
    def plot_monthly_distribution(self, dataset):
        
        dataset['raised'] = pd.to_datetime(dataset['raised'])
        dataset['month'] = dataset['raised'].dt.month
        day_counts = dataset['month'].value_counts().sort_index()

        # Plot the variation
        plt.figure(figsize=(10, 6))
        day_counts.plot(kind='bar', color='skyblue')
        plt.title('Number of tickets')
        plt.xlabel('Month')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()  
    
    def plot_ticket_distribution(self, dataset, timeframe_unit):
        """
        Plots ticket distribution (monthly, weekly, hourly).

        Parameters
        ----------
        dataset : dataframe
            Dataset analyzed.
        timeframe_unit : str
            Timeframe measurement (monthly, weekly, or hourly).

        Returns
        -------
        None.

        """
        dataset['raised'] = pd.to_datetime(dataset['raised'])
        
        plt.figure(figsize=(10, 6))
        if timeframe_unit == "monthly":
            dataset['month'] = dataset['raised'].dt.month
            counts = dataset['month'].value_counts().sort_index()    
            plt.xlabel('Month')
        elif timeframe_unit == "weekly":
            dataset['day_of_week'] = dataset['raised'].dt.day_name()
            weekday_order = list(calendar.day_name)
            dataset['day_of_week'] = pd.Categorical(dataset['day_of_week'], categories=weekday_order, ordered=True)
            counts = dataset['day_of_week'].value_counts(sort=False)
            plt.xlabel('Day of the week')
        elif timeframe_unit == "daily":
            dataset['day'] = dataset['raised'].dt.day  
            counts = dataset['day'].value_counts().sort_index()
            plt.xlabel('Day')
        elif timeframe_unit == "daily_monthly":
            plt.figure(figsize=(60, 6))
            dataset['month'] = dataset['raised'].dt.month
            dataset['day'] = dataset['raised'].dt.day  
            counts = dataset.groupby(['month', 'day']).size().sort_index()
            plt.xlabel('Month_Day')
        else:
            dataset['hour_of_the_day'] = dataset['raised'].dt.hour
            counts = dataset['hour_of_the_day'].value_counts().sort_index()
            plt.xlabel('Hour')

        counts.plot(kind='bar', color='skyblue')
        plt.title('Number of tickets')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()  
        
    def plot_families_distribution(self, dataset):
        """
        Plots the families distribution with relevance to the most common.

        Parameters
        ----------
        dataset : dataframe
            Dataset being plotted.

        Returns
        -------
        None.

        """
        plt.figure(figsize=(10, 6))
        family_counts = dataset['family'].value_counts()
        family_counts.plot(kind='bar', figsize=(10, 5))
        plt.xlabel('Families')
        plt.ylabel('Number of Instances')
        plt.title('Family Distribution in Dataset')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
            
        most_common_family = dataset['family'].value_counts().idxmax()
        family_df = dataset[dataset['family'] == most_common_family]
        family_df['date'] = family_df['raised'].dt.date
        daily_counts = family_df.groupby('date').size()
        plt.figure(figsize=(10, 6))
        plt.plot(daily_counts.index, daily_counts.values, linestyle='-')
        plt.ylim(0,20)
        plt.xlabel('Date')
        plt.ylabel('Number of Records')
        plt.title(f'Distribution of Family "{most_common_family}" Over Time')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def generate_tickets(self, thread_canceled, weight, countries, countries_path):
        """
        Main ticket generator handler (creates tickets with preliminary data).

        Parameters
        ----------
        thread_canceled : bool
            Thread status (cancels generation if TRUE).
        weight : int
            Used for the interface progress bar (deprecated).
        countries : dict
            Comprises information about the countries collected from an external file.
        countries_path : str
            Path leading to the file containing information about the countries.

        Returns
        -------
        None.

        """
        initial_time = datetime.now()
        networks_used, families_used = [], {}

        countries_chosen = np.random.choice(countries, size=self.n_tickets)
        countries_data = Configurator.get_countries_data(countries_path, countries_chosen)
        
        if self.ticket_escalation_selector:
            escalate_choices = BufferedRandomChoiceGenerator([True, False], [self.escalate_rate_percentage/100, 1 - self.escalate_rate_percentage/100], self.n_tickets)
        else:
            escalate_choices = BufferedRandomChoiceGenerator([True, False], [0, 1], self.n_tickets)
            
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Escalation: {escalate_choices}')
        outlier_choices = BufferedRandomChoiceGenerator([True, False], [self.aux_data.outlier_rate/100, 1 - self.aux_data.outlier_rate/100], self.n_tickets)
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Outliers: {outlier_choices}')

        dst_port_type = BufferedRandomChoiceGenerator(["well-known", "registered"], [0.5, 0.5], self.n_tickets)
        clients = self.get_clients(1, self.clients_number, self.n_tickets, "Client_")
        
        self.distribution_data.ticket_seasonality_selector = Utils.check_datetime_range_selected(self.start_date, self.end_date, self.distribution_data.ticket_seasonality_selector)
        
        time_slots = Utils.get_time_slots(self.distribution_data.family_time_probability_pool)
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Time Slots: {time_slots}')
        
        stime = datetime.strptime(self.start_date, '%d-%m-%Y %H:%M:%S')
        stime = stime.replace(tzinfo=pytz.utc)
        etime = datetime.strptime(self.end_date, '%d-%m-%Y %H:%M:%S')
        etime = etime.replace(tzinfo=pytz.utc)
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Start datetime: {stime}, End datetime: {etime}')

        daily_probs = Utils.apply_seasonality_distribution(self.distribution_data, self.ticket_growth_rate, stime, etime)
        smoothed_day_probs = Utils.smooth_ticket_distribution_probabilities(daily_probs)
        selected_dates = Utils.apply_weekly_distribution(self.distribution_data, smoothed_day_probs, self.n_tickets)
        selected_times = Utils.apply_daytime_distribution(self.distribution_data, self.n_tickets)

        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Build tickets")
        tickets_sorted = self.assign_ticket_preliminary_data(thread_canceled, stime.timestamp(), etime.timestamp(), countries_chosen, countries_data, clients, outlier_choices, escalate_choices, networks_used, selected_dates, selected_times)
        self.assign_ticket_family_subfamily(tickets_sorted, countries_data, dst_port_type, families_used, time_slots)    
        
        wait_time, curr_time = Utils.get_function_time_spent(initial_time)
        average_ticket_time = wait_time / self.n_tickets
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'All tickets created! Average time to generate a ticket: {average_ticket_time} seconds')
    
    def assign_ticket_preliminary_data(self, thread_canceled, stime, etime, countries_chosen, countries_data, clients, outlier_choices, escalate_choices, networks_used, selected_dates, selected_times):
        """
        Assigns preliminary data to the tickets.        

        Parameters
        ----------
        thread_canceled : bool
            Thread status (cancels generation if TRUE).
        n_tickets : int
            Number of tickets to generate.
        stime : int
            Start timestamp of the datetime generation.
        etime : int
            End timestamp of the datetime generation.
        countries_chosen : list
            Selected countries to be assigned to the tickets.
        countries_data : dict
            Comprises information about the countries selected (timezone and newtorks).
        clients : list
            Clients generated for all tickets.
        outlier_choices : BufferedRandomChoiceGenerator
            Generator for outliers to be assigned to the tickets.
        escalate_choices : BufferedRandomChoiceGenerator
            Generator for escalation to be assigned to the tickets.
        networks_used : list
            List of networks analyzed (useful for IP generation).
        selected_dates : list
            List of dates generated.
        selected_times : list
            List of times generated.

        Returns
        -------
        sorted_dict : dict
            Tickets sorted by datetime.

        """
        unsorted_tickets = {}
        
        for i in range(self.n_tickets):
            if not thread_canceled:
                country = countries_chosen[i]
                utc_datetime, timestamp = Utils.build_date(stime, etime, selected_dates[i], selected_times[i])
                    
                unsorted_tickets[i] = {}
                Utils.update_data(unsorted_tickets[i], raised = utc_datetime, raised_tsp = timestamp, country = country, allocated = utc_datetime, allocated_tsp = timestamp, temp_allocated = utc_datetime, temp_allocated_tsp = timestamp, client = clients[i], team = "", analyst = None, action = None, duration = None, duration_outlier = None, replication_status = None, similarity_analysis = False, outlier = next(outlier_choices.generate()), similar = [], escalate = next(escalate_choices.generate()))
    
                # Different clients may share the network
                if clients[i] not in self.clients_info.keys():
                    self.clients_info[clients[i]] = {}
    
                if country not in self.clients_info[clients[i]].keys():
                    self.clients_info[clients[i]][country], self.clients_info[clients[i]][country]["ips"] = {}, {}
                    self.clients_info[clients[i]][country]["networks"] = []
    
                network = Utils.get_country_network(countries_data[country]['ips'], networks_used, self.aux_data)
                networks_used.append(network)
                self.clients_info[clients[i]][country]["networks"].append(network)
                
        sorted_dict = OrderedDict(sorted(unsorted_tickets.items(), key=lambda x: x[1]['raised_tsp']))
        # For verification purposes
        if not Utils.is_dict_sorted(sorted_dict):
            print("Not sorted")
            sys.exit()
            
        return sorted_dict

    def assign_ticket_family_subfamily(self, ticket_dict, countries_data, dst_port_type, families_used, time_slots):
        """
        Assigns families and subfamilies to the tickets (family - incident type; subfamily - incident subtype)

        Parameters
        ----------
        n_tickets : int
            Number of tickets considered.
        ticket_dict : dict
            Tickets generated (with datetimes.
        countries_data : dict
            Comprises information about the countries selected (timezone and newtorks).
        dst_port_type : BufferedRandomChoiceGenerator
            Can be either well-known or registered.
        families_used : dict
            Families and subfamilies already used.
        time_slots : list
            Time of the day divided in 5-minutes slots.

        Returns
        -------
        None.

        """
        
        ordered_tickets = {} 
        keys = list(ticket_dict.keys())
        
        for l in range(self.n_tickets):
            ordered_tickets[l] = ticket_dict[keys[l]]
            ordered_tickets[l]["id"] = l
            
            if self.distribution_data.distribution_mode == "normal":
                Utils.get_family_subfamily(self.family_pool, self.subfamily_pool, self.distribution_data, ordered_tickets[l], self.suspicious_data, self.aux_data, self.ip_selector, time_slots, families_used)
            else:
                family = random.choice(list(self.family_pool.keys()))
                ordered_tickets[l]["family"] = family
                ordered_tickets[l]["subfamily"] = f'{family}_{random.randint(1, self.family_pool[family]["subtypes"])}' 
                Utils.update_subfamily_pool(ordered_tickets[l]["subfamily"], self.subfamily_pool, self.suspicious_data)
            
            self.assign_extra_features(ordered_tickets[l], countries_data, dst_port_type)
            
        for team in self.analysts_info.keys():
            self.tickets[team] = {}
            
        first_team = list(self.analysts_info.keys())[0]
        for k in range(len(ordered_tickets)):
            self.tickets[first_team][k] = ordered_tickets[k]
                
    def assign_extra_features(self, ticket, countries, dst_port_type):
        """
        Assigns extra features to each ticket (priority, suspicious, and others)

        Parameters
        ----------
        ticket : dict
            Comprises information about the current ticket.
        countries : dict
            Comprises information about the countries collected from an external file.
        dst_port_type : BufferedRandomChoiceGenerator
            Can be either well-known or registered.

        Returns
        -------
        None.

        """
        family = ticket["family"]
        subfamily = ticket["subfamily"]

        ticket['suspicious'] = Utils.check_ticket_suspicious(ticket, self.subfamily_pool[subfamily]['suspicious'], self.suspicious_data.suspicious_countries)
        ticket['priority'] = self.family_pool[family]["priority"]
        ticket['extra_features'] = self.family_pool[family]["extra_features"]

        Utils.assign_ticket_ip(self.family_pool[family]["ip"], ticket, self.clients_info, self.suspicious_data.suspicious_ips, self.ips_pool, self.ip_selected_idx, countries, self.aux_data, dst_port_type)
        #Utils.set_extra_features_values(ticket, self.family_pool[family]["extra_features"])
        
    def get_tickets_statistics(self, team_analytics, tickets_number, wait_times, resolution_times):
        """
        Gets statistics about the treated tickets (wait time, tickets shifted for later date, among other features).

        Parameters
        ----------
        teams_analytics : dict
            Comprises information about the teams and their shifts
        tickets_number : int
            Number of tickets analyzed.
        wait_times : list
            Comprises information about the time each ticket had to wait to be treated.
        resolution_times : list
            Comprises information about the time taken by operators to fix each ticket.
            
        Returns
        -------
        None.

        """
        tickets_shifted = 0
        for team in team_analytics:
            tickets_shifted += team_analytics[team]["scheduled"]["others"]
            tickets_shifted += team_analytics[team]["scheduled"]["other_day"]
            tickets_shifted += team_analytics[team]["scheduled"]["other_shift"]
           
        messages = [
            f'N tickets shifted: {tickets_shifted}',
            f'Percentage of tickets shifted: {round((tickets_shifted/tickets_number), 2)}',
            f'Wait time average: {round((sum(wait_times) / len(wait_times)), 2)}',
            f'Wait time standard deviation: {round(np.std(wait_times), 2)}',
            f'Resolution time average: {round((sum(resolution_times) / len(resolution_times)), 2)}']
        
        for msg in messages:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, msg)
        
    def evaluate_team_performance(self, teams_analytics):
        """
        Evaluates the teams performance over the different shifts

        Parameters
        ----------
        teams_analytics : dict
            Comprises information about the teams and their shifts
        Returns
        -------
        None.

        """
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "---  Team Evaluation ---")
        for team in teams_analytics:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Team {team} has {len(self.analysts_info[team]["analysts"])} analysts: {list(self.analysts_info[team]["analysts"].keys())}')
            
            shift_performance = {}
            for shift in teams_analytics[team]["shifts"]:
                shift_performance[shift] = {}
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Shift {shift} treated {len(teams_analytics[team]["shifts"][shift].keys())} tickets. Ids: {list(teams_analytics[team]["shifts"][shift].keys())}')

                total_wait_time, total_time_spent = 0,0
                for ticket_id in teams_analytics[team]["shifts"][shift]:
                    total_wait_time += teams_analytics[team]["shifts"][shift][ticket_id]["wait_time"]
                    total_time_spent += teams_analytics[team]["shifts"][shift][ticket_id]["time_spent"]
                
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Total amount of time spent (minutes): {total_time_spent}. Average time spent (in minutes): {total_time_spent/len(teams_analytics[team]["shifts"][shift].keys())}')
                shift_performance[shift]["n_tickets"] = len(teams_analytics[team]["shifts"][shift].keys())
                shift_performance[shift]["time_spent"] = total_time_spent
                shift_performance[shift]["wait_time"] = total_wait_time
            
            Utils.analyse_shifts_performance(shift_performance, teams_analytics[team]["shifts"], self.analysts_info[team]["analysts"])
            
            messages = [
                f'Number of Scheduled tickets: {teams_analytics[team]["scheduled"]["other_day"] + teams_analytics[team]["scheduled"]["other_shift"] + teams_analytics[team]["scheduled"]["others"]}',
                f'Number of Scheduled tickets to other day: {teams_analytics[team]["scheduled"]["other_day"]}',
                f'Number of Scheduled tickets to other shift: {teams_analytics[team]["scheduled"]["other_shift"]}',
                f'Number of Scheduled tickets later in their shift: {teams_analytics[team]["scheduled"]["others"]}']
            
            for msg in messages:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, msg)
            
    def evaluate_real_synthetic_datasets(self, dataset, real_dataset, real_family_probs, family_mapping, show_plots):
        """
        Compares the real and synthetic dataset using similarity measures and visual analysis

        Parameters
        ----------
        dataset : dataframe
            Dataset generated.
        real_dataset : dataframe
            Real Dataset.
        real_family_probs: dict
            Comprises the probabilities of the real families.
        family_mapping : dict
            Maps synthetic families with real ones.
        show_plots : bool
            Show or do not show plots about the comparison between real and synthetic datasets.

        Returns
        -------
        None.

        """
        Utils.debug_and_log_data(True, self.aux_data.logger, "--- Comparison between the Real and Synthetic Datasets ---")
        synthetic_family_probs = dataset['family'].value_counts(normalize=True).sort_index()
    
        print("Real probs:", real_family_probs)
        print("Synthetic probs:", synthetic_family_probs)
        kl_divergence = kl_div(real_family_probs, synthetic_family_probs).sum()
        hellinger_distance = np.sqrt(np.sum((np.sqrt(real_family_probs) - np.sqrt(synthetic_family_probs)) ** 2)) / np.sqrt(2)
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Kl_divergences: {kl_divergence}. Hellinger distance: {hellinger_distance}')
        
        synthetic_families = list(dataset['family'].unique())
        filtered_df = real_dataset[real_dataset["Family"].isin(synthetic_families)]
        ks_statistic, p_value = stats.ks_2samp(filtered_df["Family"], dataset["family"])
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'KS Statistic: {ks_statistic}. P-value: {p_value}')
        
        #real_feature_stats = real_dataset["Family"].describe()
        #synthetic_feature_stats = dataset["family"].describe()
        #print("Real Data Stats:", real_feature_stats)
        #print("Synthetic Data Stats:", synthetic_feature_stats)
    
        if show_plots:
            dataset['Year/month'] = dataset['raised'].apply(lambda x: datetime.strftime(x, '%m'))
            a4_dims = (30, 12)
            fig, ax = plt.subplots(figsize=a4_dims)
            freq = dataset.pivot_table(index="Year/month", columns="family", aggfunc="size", fill_value=0)
            families = sorted(freq.columns)
            months = freq.index
            cumulative = np.zeros(len(months))
            freq = freq[families]
        
            for family in families:
                plt.barh(months, freq[family], left=cumulative, label=family)
                cumulative += freq[family]
            plt.xlabel("Ticket Frequency")
            plt.ylabel("Months")
            plt.xlim(0, 830)
            #plt.title("Stacked Horizontal Bar Chart of Family Frequency by Year/Month")
            plt.legend(fontsize = 24, bbox_to_anchor=(1.01, 0.5) , loc='center left', ncol= 1, borderaxespad=0.,)
            plt.tight_layout()
            plt.savefig('Plots\\generated_families_month.svg', format="svg")
            plt.show()
            
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Generated families: {self.family_pool.keys()}')
            real_families, real_families_mean = [], []
            families_mapping = {}

            for gen_family in self.family_pool.keys():
                real_fam = self.family_pool[gen_family]["real_family"]
                real_families.append(real_fam)
                real_families_mean.append(self.family_mean_duration[real_fam])    
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Real families: {real_families}. Real families values: {real_families_mean}')

            for family in self.family_pool.keys():
                real_family = self.family_pool[family]["real_family"]
                families_mapping[family] = real_family
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Families mapping: {families_mapping}')

            zipped = list(zip(real_families, real_families_mean))
            original_family_distribution = pd.DataFrame(zipped, columns=['family', 'mean'])
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Original: {original_family_distribution}')

            family_duration_distribution = dataset.groupby('family')['duration'].mean().reset_index(name="mean")
            family_duration_distribution_mapped=family_duration_distribution.replace({"Family": families_mapping})
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Generated Mean Time spent mapped: {family_duration_distribution_mapped}')

            x = np.arange(len(real_families))
            width = 0.2

            fig, axs = plt.subplots(1,1, figsize = (18,6))
            axs.bar(x - width/2, family_duration_distribution['mean'], width = width, label = "Generated", edgecolor = "black")
            axs.bar(x + width/2, original_family_distribution['mean'], width = width, label = "Real", edgecolor = "black")

            axs.set_xticks(x)
            axs.set_xticklabels(list(self.family_pool.keys()))
            axs.set_title("Families Mean Resolution Duration")
            axs.set_xlabel("Families", fontsize=20)
            axs.set_ylabel("Time (minutes)", fontsize=20)
            axs.legend(title = "Datasets", fontsize = 14, title_fontsize = 20)
            plt.savefig("Plots\\teste_mean_fix_duration.svg", format="svg")