from Code.Generator.TicketGenerator import TicketGenerator
from Code.Utils import Utils
from Code.AnalystEmulation import AnalystEmulation
from Code.Configurator import Configurator

from datetime import datetime
import psutil, uuid, tracemalloc

class DatasetGenerator:
    # Preparates the dataset generation
    def __init__(self, generation, logger_active, config_path):
        self.gen_id = uuid.uuid4()
        self.canceled = generation.canceled 
        self.domain = generation.args[0]
        self.generation_params = generation.args[1]
        self.treatment_params = generation.args[2]
        self.countries = generation.args[3]
        self.output_params = generation.args[4]
        self.output_path = f'{config_path}/{self.domain}'
        self.logger = Utils.create_log(self.output_path, f'Generation_Log_{self.gen_id}', logger_active)
        self.logger_active = logger_active

    # Generates the Train and Test Datasets
    def build_datasets(self, countries_path):
    
        print("Memory spent by interface and imports: " + str(psutil.Process().memory_info().rss / (1024 * 1024)) + " MB")
        print("Start Generation...")        
        print("Domain:", self.domain)
        print("Number of train tickets:", self.generation_params["train_ticket"])
        print("Number of test tickets:", self.generation_params["test_ticket"])
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
        Utils.debug_and_log_data(True, self.logger_active, self.logger, f'Memory spent by interface and imports: {psutil.Process().memory_info().rss / (1024 * 1024)} MB\n###### GENERATION DEBUGGING ######\n')
        tracemalloc.start()

        if self.generation_params["reset_analysts_data"]:
            self.generation_params["analysts_skills"], updated_data = Utils.reset_analysts_data(self.generation_params, self.treatment_params["shifts"], self.logger)
            Configurator.update_configuration_data("analysts_info", updated_data, self.domain, f'{self.output_path}/Init_cfg.yaml')

        ticket_generator = TicketGenerator(self.gen_id, self.domain, self.generation_params, self.logger, self.logger_active)
        initial_time = datetime.now()
        if not self.canceled:
            ticket_generator.get_families_probabilities(self.canceled, self.generation_params["family_mapping"], 10, 6)
            wait_time, curr_time = Utils.get_function_time_spent(initial_time)            
            Utils.debug_and_log_data(True, self.logger_active, self.logger, f'Family generation Time spent: {wait_time} seconds\nFamilies probabilities memory: {psutil.Process().memory_info().rss / (1024 * 1024)} MB')
    
        if not self.canceled:
            ticket_generator.generate_tickets(self.canceled, 20, self.countries, countries_path)
            wait_time, curr_time = Utils.get_function_time_spent(curr_time)
            Utils.debug_and_log_data(True, self.logger_active, self.logger, f'Ticket generation Time spent: {wait_time} seconds\nTickets generation memory: {psutil.Process().memory_info().rss / (1024 * 1024)} MB')

        if not self.canceled:
            ticket_generator.generate_actions(self.canceled, 5, "train", True)
            wait_time, curr_time = Utils.get_function_time_spent(curr_time)
            Utils.debug_and_log_data(True, self.logger_active, self.logger, f'Family and subfamily Actions Generation Time spent: {wait_time} seconds')
 
        ticket_treatment = AnalystEmulation(self.gen_id, self.treatment_params, ticket_generator.analysts_info, ticket_generator.family_pool, ticket_generator.subfamily_pool, ticket_generator.family_steps_pool, ticket_generator.special_steps, ticket_generator.aux_data, self.generation_params["seed"])
        if not self.canceled:
            ticket_generator.train_tickets, family_subtechniques = ticket_treatment.process_tickets(self.canceled, 15, ticket_generator.train_tickets)
            wait_time, curr_time = Utils.get_function_time_spent(curr_time)
            Utils.debug_and_log_data(True, self.logger_active, self.logger, f'Analyst Train Assignment Time spent: {wait_time} seconds\nTrain Tickets assignment memory: {psutil.Process().memory_info().rss / (1024 * 1024)} MB')

        if not self.canceled:
            ticket_generator.output_train_dataset(self.canceled, 5, self.generation_params["format_selected_idx"], self.output_params, ticket_treatment.actions_similarity, self.generation_params["family_mapping"], False, family_subtechniques)
            wait_time, curr_time = Utils.get_function_time_spent(curr_time)
            Utils.debug_and_log_data(True, self.logger_active, self.logger, f'Train Output Time spent: {wait_time} seconds\nOutput Train Tickets memory: {psutil.Process().memory_info().rss / (1024 * 1024)} MB')

        if not self.canceled:
            ticket_generator.output_test_dataset(self.canceled, 20, self.generation_params["format_selected_idx"], "unsolved")
            generator_info_file = f'{self.output_path}/Generation_data_{self.gen_id}.json'
            Utils.save_generator_data(generator_info_file, ticket_treatment.family_pool, ticket_treatment.family_steps_pool,
                                             ticket_treatment.subfamily_pool, ticket_treatment.subfamily_steps_speeds, ticket_treatment.special_steps)
            input_info_file = f'{self.output_path}/Input_data_{self.gen_id}.json'
            Utils.save_input_data(input_info_file, self.generation_params, self.treatment_params)
        
            wait_time, curr_time = Utils.get_function_time_spent(curr_time)
            Utils.debug_and_log_data(True, self.logger_active, self.logger, f'Unsolved Test Output Time spent: {wait_time} seconds\nUnsolved Output Test Tickets memory: {psutil.Process().memory_info().rss / (1024 * 1024)} MB')

            wait_time, curr_time = Utils.get_function_time_spent(curr_time)
            Utils.debug_and_log_data(True, self.logger_active, self.logger, f'Test Output Time spent: {wait_time} seconds\nOutput Complete Test Tickets memory: {psutil.Process().memory_info().rss / (1024 * 1024)} MB')

        time_delta = datetime.now() - initial_time
        generation_time = time_delta.total_seconds()
        print("Total Generation time (seconds):", generation_time)
        current, peak = tracemalloc.get_traced_memory()
        print(f"Current memory usage: {current / 10**6} MB; Peak: {peak / 10**6} MB")
        tracemalloc.stop()
        #Utils.debug_and_log_data(True, self.logger_active, self.logger, f'Final memory usage (RAM): {psutil.Process().memory_info().rss / (1024 * 1024)} MB\nMemory usage (RAM) from the system: {psutil.Process().memory_percent()} %')