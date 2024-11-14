let graphDataArry = [];

async function fetchGraphData() {
    try {
        const response = await fetch('/graph-data');
        let data = await response.json();
        data = {
            "2024-11-09T10:00:00": [
                { "team_id": 1, "mean_temp": 22.5, "mean_humi": 60, "mean_illu": 300 }
            ],
            "2024-11-10T10:00:00": [
                { "team_id": 1, "mean_temp": 22.5, "mean_humi": 60, "mean_illu": 300 }
            ],
            "2024-11-10T19:00:00": [
                { "team_id": 1, "mean_temp": 22.245, "mean_humi": 54.22, "mean_illu": 284.08 },
                { "team_id": 2, "mean_temp": 23.74, "mean_humi": 50.46, "mean_illu": 482.632 }
            ]
        };
        graphDataArry = data; // Save the fetched data
        console.log(graphDataArry);
        const preparedData = prepareChartData(graphDataArry); 
        console.log(preparedData)
    } catch (error) {
        console.error('Error fetching graph data:', error);
    }
}
function prepareChartData(sensorData) {
    const labels = Object.keys(sensorData); // Timestamps as labels
    const teams = new Set(); // To store unique team_ids
    
    // Loop through the data to gather unique teams
    Object.entries(sensorData).forEach(([timestamp, teamsData]) => {
      teamsData.forEach(team => {
        teams.add(team.team_id); // Add team_id to the set (only unique ids will be kept)
      });
    });
  
    // Utility function to generate a dataset for each physical quantity
    const createMetricDataset = (metric, label) => {
      return Array.from(teams).map(teamId => {
        return {
          label: `${label} Team ${teamId}`,
          data: labels.map(timestamp => {
            const teamData = sensorData[timestamp].find(team => team.team_id === teamId);
            return teamData ? teamData[metric] : null; // Handle missing data with null
          }),
          fill: false, // If you're using a line chart (set to true for filled area charts)
          borderColor: getColorByTeamId(teamId), // Random color for each line
          tension: 0.1 // Optional, smooth the line
        };
      });
    };
  
    // Create separate datasets for each metric
    const tempDatasets = createMetricDataset('mean_temp', 'Temperature');
    const humiDatasets = createMetricDataset('mean_humi', 'Humidity');
    const illuDatasets = createMetricDataset('mean_illu', 'Illumination');
    
    // Combine all datasets into a single chartData object
    const chartData = {
      labels: labels, // Timestamps as x-axis labels
      datasets: [
        ...tempDatasets,   // Temperature datasets
        ...humiDatasets,   // Humidity datasets
        ...illuDatasets    // Illumination datasets
      ]
    };
  
    return chartData;
  }

function getColorByTeamId(teamId) {
    const teamColors = {
        1: 'blue',
        2: 'black',
        3: 'green',
        4: 'pink',
        5: 'red',
        6: 'yellow'
    };

    // Return the color associated with the teamId, defaulting to 'gray' if no match is found
    return teamColors[teamId] || 'gray';  // If the teamId doesn't exist in the object, return 'gray'
}

// Start fetching and plotting data
fetchGraphData();
