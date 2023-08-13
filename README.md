# Open Field Statistics

## Description

**Open Field Statistics** is a GUI application for analyzing animal's locomotor activity in an open field box, tracked by IR-beams crossing. It receives [raw data](#raw-data) from beams in a .csv file, visualizes animal's trajectory and calculates some behavioral [statistics](#features) in user-defined zones and time periods. The output statistics can then be saved in a new spreadsheet.

This application was developed to process the output of a commercial [third-party](http://new.novatorlab.ru/en/) system and software with closed source code. The external program operates the hardware, receives signals from the IR-beams and produces the .csv file with the raw data. However, it fails to perform a comprehensive and scientifically relevant analysis of the data, motivating development of the current application.

Although this application is originally narrow-purposed, reflecting constraints of the third-party software, it can easily be repurposed for a wider range of custom photobeam setups, provided that they produce represent data in a compatible format.

This implementation is clearly an overkill for the task, but it served me as practice in full-stack development and deployment of GUI applications. 

## Hardware and raw data

The third-party apparatus is a 40x40x30 cm box with two 16x16 photobeam frames. The lower frame tracks animal's horizontal activity (**X** and **Y** coordinates), and the upper frame detects the vertical activity (rearings). 

The raw data produced by external software operating the system itself (and the input data for the current application) is a ;-separated .csv file with six columns:

- timestamp with update rate of ~12 Hz
- **X1** and **X2** - leftmost and rightmost intersected beams by the X axis
- **Y1** and **Y2** - downmost and uppermost intersected beams by the Y axis
- **Z** with ```True```/```False``` values, reflecting breaks of any of the upper beams

Note that since only the extreme coordinates are shown in the table, the program cannot differentiate between two objects simultaneously breaking photobeams.

<img height="370" align="top" alt="Example_raw_data_Excel" src="https://github.com/ArseniyPelevin/open-field-statistics/assets/106020155/afbc167b-7869-4ba3-bcd9-2552b0648a9d" >
<img height="370" align="top" alt="Raw_data_representation" src="https://github.com/ArseniyPelevin/open-field-statistics/assets/106020155/e4a9a91e-e305-4d1b-b5e3-d28a89b5339e">

## Interface

<img width="710" alt="Application_GUI" src="https://github.com/ArseniyPelevin/open-field-statistics/assets/106020155/1f9e1bc3-ea6d-441e-84bd-00657ee9cb34">

## Features

### Time intervals

User can select a time range of the experiment to analyze (slider in the bottom-left corner). It can be useful, for example, to exclude a habituation period from the beginning of the record. The table and the output file will show both **Total time** and **Selected time** statistics.

The *Selected time* can be further divided into periods of user-defined length in seconds. For each of the periods separate statistics will be shown.

### Zones

The statistics is calculated for the Whole field and for user-defined zones. **Seven** types of zone selection can be chosen with buttons to the left of the map:

Three options divide the whole field into two predefined zones.

![Area button - vertical halves](https://github.com/ArseniyPelevin/open-field-statistics/blob/master/Area_Buttons_Pixmaps/Vertical_halves.png)
 Two vertical halves
 
![Area button - horizontal halves](https://github.com/ArseniyPelevin/open-field-statistics/blob/master/Area_Buttons_Pixmaps/Horizontal_halves.png)
 Two horizontal halves

![Area button - wall/center](https://github.com/ArseniyPelevin/open-field-statistics/blob/master/Area_Buttons_Pixmaps/Wall.png)
 One central and one peripheral zone. This field division is often used in behavioral science to assess anxiety and stress in animals.

<img width="318" alt="Zones_horizontal_halves" src="https://github.com/ArseniyPelevin/open-field-statistics/assets/106020155/a539ab67-fe92-487d-9d19-09b5981f8e18">
<img width="318" alt="Zones_wall_center" src="https://github.com/ArseniyPelevin/open-field-statistics/assets/106020155/e45ff07e-6ab1-4cb9-985b-bf691145d6c6">
<br><br>

Four options allow user to set their own zones. The maximal number of custom zones is 4. After completing selection of a new zone user has to press ```Add zone``` button. Only one type of custom zone can be used at once (I am planning to change it in the future).

![Area button - one cell](https://github.com/ArseniyPelevin/open-field-statistics/blob/master/Area_Buttons_Pixmaps/Cell.png)
 One cell at a time. Allows the most flexible zone definition

![Area button - vertical line](https://github.com/ArseniyPelevin/open-field-statistics/blob/master/Area_Buttons_Pixmaps/Column.png)
 A vertical line

![Area button - horizontal line](https://github.com/ArseniyPelevin/open-field-statistics/blob/master/Area_Buttons_Pixmaps/Row.png)
 A horizontal line

![Area button - concentric square](https://github.com/ArseniyPelevin/open-field-statistics/blob/master/Area_Buttons_Pixmaps/Square.png)
 A concentric square

<img width="318" alt="Zones_vertical_lines" src="https://github.com/ArseniyPelevin/open-field-statistics/assets/106020155/743bd26d-d802-4cd9-9f3a-93a59e560c75">
<img width="318" alt="Zones_concentric_squares" src="https://github.com/ArseniyPelevin/open-field-statistics/assets/106020155/8b971cc5-da56-48fa-8727-c01e30945d2e">

### Statistics 

For each zone/period the following **five** behavioral statistics are calculated:

- **Time (s)** spent in this zone (for the Whole field - the length of this period)
- **Distance (cm)**
- **Velocity (cm/s)**
- **Rearings number**
- **Rearings time (s)**

## Output

Output is a .csv file. By default user is prompted to save it to the save folder as the input in the format 'Input_file_name_statistics.csv', but both location and name can be changed.

<img width="407" alt="Output_table" src="https://github.com/ArseniyPelevin/open-field-statistics/assets/106020155/cf51499b-50d3-4d9a-a71f-99136e1c4a38">

## Future development

- [ ] Add option to choose field configuration and number of beams
- [ ] Make zone selection more flexible: allow different zone types simultaneously, support custom zone elements of different sizes, add drag-select
- [ ] Add number of zone entering statistics
- [ ] Save parameters
- [ ] Add animation of the recording with different speed

## Credits

This software was developed as part of my research work in the Laboratory of Neurobiology and Molecular Pharmacology of the Institute of Translational Biomedicine of St Petersburg University, under the scientific supervision of Dr. Anna B. Volnova <a href="https://orcid.org/0000-0003-0724-887X"><img alt="ORCID logo" src="https://info.orcid.org/wp-content/uploads/2019/11/orcid_16x16.png" width="16" height="16" /></a>
