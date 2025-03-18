# SNOOKER

SNOOKER is a dataset generator designed to create synthetic helpdesk datasets with diverse distributions based on the chosen generation domain selected (currently, only Cybersecurity is implemented). This generator produces training and test datasets consisting of resolved tickets and test datasets comprising open tickets. Each dataset includes simulated incidents with varying incidents properties, managed by different teams of simulated operators, each exhibiting unique traits. These tickets are treated with emulated procedures and can be escalated, prioritized and scheduled, depending on certain conditions

# Libraries
- Python
- PyQT


# Dataset Settings

The user may follow a quick generation or build a custom generation with the following parameters:

| **Configurations**             | **Description**                                          |
|--------------------------------|----------------------------------------------------------|
| Train and Test Tickets         | Number of train and test tickets                         |
| Ticket growth type             | Increase, decrease or maintain in upcoming years         |
| Ticket growth rate             | Ticket growth rate in each year                          |
| Date range                     | Ticket date interval                                     |
| Clients                        | Number of clients                                        |
| Escalation                     | Escalate to higher teams                                 |
| Escalation probability         | Escalation likelihood                                    |
| Seasonality                    | Seasonality over the year                                |
| Similarity detection           | Detect similar tickets                                   |
| Min, Max occurrences           | Maximum and minimum number of occurrences for escalation |
| Min, Max detection interval    | Maximum and minimum minutes interval sharing the family and country | 
| Outlier                        | Include outliers                                         | 
| Outlier rate                   | Outlier rate                                             | 
| Outlier cost                   | Procedures extra cost                                    | 
| **Family and Subfamily**       |                                                          | 
| Generation                     | Default families (external file) or custom               | 
| Seasonality                    | Seasonality over the year                                | 
| Families                       | Number of incident types (e.g. VPN)                      | 
| Min, Max subfamilies           | Minimum and maximum number of subfamilies (e.g. VPN_1)   | 
| Suspicious probability         | Probability of a subfamily being suspicious              | 
| Distribution type              | Normal or Uniform Distribution                           | 
| Day distribution               | Likelihood to occur equally during the day, higher on daylight or nighttime | 
| Week distribution              | Likelihood to occur equally during the week, higher on weekdays or weekends | 
| New Family and Subfamily       | New family and subfamily likelihood                      | 
| **Technique Configurations**   |                                                          | 
| Techniques                     | Number of techniques in each family                      | 
| Min, Max subtechniques         | Minimum and maximum number of subtechniques              | 
| Min, Max subtechnique duration | Maximum and minimum duration of each subtechnique        | 
| Min, Max subtechnique rate     | Maximum and minimum frequency of each subtechnique       | 
| Disparity detection            | Detect different procedures                              | 
| Max disparity                  | Maximum number of differences between analyst and subfamily actions | 
| **Teams**                      | 	                                                        | 
| Generation                     | Standard or custom generation                            | 
| Ticket assignment              | Tickets are assigned to the lowest team (hierarchical allocation), or a ticket percentage is allocated to each team |
| Work shift lineament           | Have teams with their work shifts balanced               |
| **Analysts**                   |                                                          |
| Name and Team                  | Analyst name and team assigned                           |
| Shift                          | Analyst shift                                            |
| Speed and Growth               | Analyst resolution speed and growth rate                 |
| Risk                           | Probability of an analyst accept recommendations         | 
| Subfamily action probability   | Likelihood to use the subfamily predefined action        | 
| Repeat action probability      | Likelihood to use the previously action in the same subfamily |
| Min, Max learning              | Minimum and maximum incident counter for analyst improvement | 

The first table presents the configurable parameters within SNOOKER main interface. Various parameters related to the tickets, incident types, techniques available, teams, analysts, and other properties can tuned.

# Domain Settings

| **Configurations**       | **Description**                                     |
|--------------------------|-----------------------------------------------------|
| IP                       | Include IPs                                         |
| IP type                  | IPv4 or IPV6                                        |
| Suspicious               | Include suspicious countries                        |
| Suspicious countries     | List of suspicious countries                        |
| Suspicious analysis      | Date interval for the analysis of suspicious behaviour |
| Excluded analysis        | List of days with disabled suspicious analysis      |

The secondary interface allows the personalization of Cybersecurity configurations, such as IP-related data and the analysis of suspicious activity which simulates the existence of countries with higher likelihood of orchestrating cyberattacks during certain periods of the day.

# Input

SNOOKER utilizes three data sources:
- Real dataset (Optional) - SNOOKER extracts information about the tickets and incidents distribution over the timeframe studied to use it in the ticket generation. Moreover, it collects data about the procedure timeline (timestamps of individual steps) also to personalize the actions available by the simulated operators**Note:** Changes must be made to the code concerned with the reading/processing of the real dataset. The private dataset used to test this feature is not available;

- Country dataset - results from merging data about the countries (timezones, continent, and capital) with IPv4 geographical location information (networks and IPs);

- Configuration File - essentially contains default settings to help generate standard datasets. It possesses information regarding existent teams and their analysts, default families and their attributes, work shift data, day distribution, and other details.

# Reference
- Article

For further inquiries, contact me at: leosfpt@hotmail.com

Licensed under [![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
