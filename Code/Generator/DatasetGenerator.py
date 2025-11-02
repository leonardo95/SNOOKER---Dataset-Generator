"""
Created on Wed Dec 16 21:42:16 2020

@author: Leonardo Ferreira
@goal: Manages the main processes of the generator
"""

from Code.Generator.TicketGenerator import TicketGenerator
from Code.Utils import Utils
from Code.AnalystEmulation import AnalystEmulation
from Code.Configurator import Configurator

from datetime import datetime
import psutil, uuid

class DatasetGenerator:
    def __init__(self, generation, logger_active, config_path):
        """
        Preparates the dataset generation.

        Parameters
        ----------
        generation : Generator
            Comprises all configurations defined in the interface.
        logger_active : bool
            Enable or disable logger.
        config_path : str
            Relative path for further processing.

        Returns
        -------
        None.

        """
        self.gen_id = uuid.uuid4()
        self.canceled = generation.canceled 
        self.domain = generation.args[0]
        self.generation_params = generation.args[1]
        self.treatment_params = generation.args[2]
        self.countries = generation.args[3]
        self.output_params = generation.args[4]
        self.cpu_times_before = generation.args[5]
        self.cpu_usage_before = generation.args[6]
        self.output_path = f'{config_path}/{self.domain}'
        self.logger = Utils.create_log(self.output_path, f'Generation_Log_{self.gen_id}', logger_active)

    def build_datasets(self, countries_path):
        """
        Generates datasets with different types of tickets.        

        Parameters
        ----------
        countries_path : str
            Countries file path.

        Returns
        -------
        None.

        """
        
        print("Memory spent by interface and imports: " + str(psutil.Process().memory_info().rss / (1024 * 1024)) + " MB")
        print("Start Generation...")        
        print("Domain:", self.domain)
        print("Number of tickets:", self.generation_params["n_tickets"])
        print("Number of Families:", self.generation_params["families_number"])
        print("Types of Families:", self.generation_params["family_selection"])
        print("Minimum number of Families:", self.generation_params["minsubfamilies_number"])
        print("Maximum number of Families:", self.generation_params["maxsubfamilies_number"])
        print("Number of Techniques:", self.generation_params["techniques_number"])
        print("Minimum number of sub techniques:", self.generation_params["minsubtechniques_number"])
        print("Maximum number of sub techniques:", self.generation_params["maxsubtechniques_number"])
        print("Outlier Rate:", self.generation_params["outlier_rate"])
        print("Debug Mode:", self.generation_params["debug"])
        print("Shifts Mode:", self.generation_params["balanced_shifts"])
        print("Plots:", self.generation_params["print_plots"])
        print("Distribution:", self.generation_params["distribution_mode"])
        print("Probability of using subfamily action:", self.treatment_params["analyst_subfamily_action_probability"])
        print("Probability of using the same prev action:", self.treatment_params["analyst_same_action_probability"])
        print("Family seasonality:", self.generation_params["family_seasonality_selector"])
        print("Family default mode:", self.generation_params["use_default_family"])

        Utils.set_seed(self.generation_params["seed"])
        shifts = Utils.split_day_shifts(int(self.generation_params["shifts"]))
        print("Shifts:", shifts)
        if self.generation_params["reset_analysts_data"]:
            self.generation_params["analysts_skills"], updated_data = Utils.reset_analysts_data(self.generation_params, shifts, self.logger)
            Configurator.update_configuration_data("analysts_info", updated_data, self.domain, f'{self.output_path}/Init_cfg.yaml')

        ticket_generator = TicketGenerator(self.gen_id, self.generation_params, self.logger)
        initial_time = datetime.now()
        if not self.canceled:
            ticket_generator.get_families_probabilities(self.canceled, self.generation_params, 10, 6)
            wait_time, curr_time = Utils.get_function_time_spent(initial_time)            
            Utils.debug_and_log_data(True, self.logger, f'Family generation Time spent: {wait_time} seconds\nFamilies probabilities memory: {psutil.Process().memory_info().rss / (1024 * 1024)} MB')
    
        if not self.canceled:
            ticket_generator.generate_tickets(self.canceled, 20, self.countries, countries_path)
            wait_time, curr_time = Utils.get_function_time_spent(curr_time)
            Utils.debug_and_log_data(True, self.logger, f'Ticket generation Time spent: {wait_time} seconds\nTickets generation memory: {psutil.Process().memory_info().rss / (1024 * 1024)} MB')

        if not self.canceled:
            ticket_generator.generate_actions(self.canceled, 5, True)
            wait_time, curr_time = Utils.get_function_time_spent(curr_time)
            Utils.debug_and_log_data(True, self.logger, f'Family and subfamily Actions Generation Time spent: {wait_time} seconds')
 
        ticket_treatment = AnalystEmulation(self.gen_id, self.treatment_params, ticket_generator.analysts_info, ticket_generator.family_pool, ticket_generator.subfamily_pool, ticket_generator.family_steps_pool, ticket_generator.special_steps, shifts, ticket_generator.aux_data, self.generation_params["seed"])
        if not self.canceled:
            ticket_generator.tickets, family_subtechniques = ticket_treatment.process_tickets(self.canceled, 15, ticket_generator.tickets)
            wait_time, curr_time = Utils.get_function_time_spent(curr_time)
            Utils.debug_and_log_data(True, self.logger, f'Analyst Assignment Time spent: {wait_time} seconds\nTickets assignment memory: {psutil.Process().memory_info().rss / (1024 * 1024)} MB')

        if not self.canceled:
            ticket_generator.output_dataset(self.canceled, 5, self.generation_params["format_selected_idx"], self.output_params, ticket_treatment.actions_similarity, shifts, self.generation_params["family_mapping"], True, self.generation_params["real_family_probs"], self.generation_params["real_dataset"], family_subtechniques, "Wait time", "real")
            wait_time, curr_time = Utils.get_function_time_spent(curr_time)
            Utils.debug_and_log_data(True, self.logger, f'Dataset Output Time spent: {wait_time} seconds\nDataset Output memory: {psutil.Process().memory_info().rss / (1024 * 1024)} MB')

        if not self.canceled:
            generator_info_file = f'{self.output_path}/Generation_data_{self.gen_id}.json'
            Utils.save_generator_data(generator_info_file, ticket_treatment.family_pool, ticket_treatment.family_steps_pool,
                                             ticket_treatment.subfamily_pool, ticket_treatment.subfamily_steps_speeds, ticket_treatment.special_steps)
            input_info_file = f'{self.output_path}/Input_data_{self.gen_id}.json'
            Utils.save_input_data(input_info_file, self.generation_params, self.treatment_params)

            wait_time, curr_time = Utils.get_function_time_spent(curr_time)
            Utils.debug_and_log_data(True, self.logger, f'Generator and Input storage time spent: {wait_time} seconds\nGenerator and Input storage memory: {psutil.Process().memory_info().rss / (1024 * 1024)} MB')

        time_delta = datetime.now() - initial_time
        generation_time = time_delta.total_seconds()
        print("Total Generation time (seconds):", generation_time)