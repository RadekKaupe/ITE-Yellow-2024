let graphDataArry = [];

async function fetchGraphData() {
    try {
        const response = await fetch('/graph-data');
        // const data = await response.json();
        let data = {
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

  // Initialize an array for each team's dataset
  const datasets = Array.from(teams).map(teamId => {
    return {
      label: `Team ${teamId}`,
      data: labels.map(timestamp => {
        // Find the team data for the current timestamp
        const teamData = sensorData[timestamp].find(team => team.team_id === teamId);
        return teamData ? teamData.mean_temp : null; // Handle missing data with null
      }),
      fill: false, // If you're using a line chart
      borderColor: getColorByTeamId(teamId), // Random color for each line
      tension: 0.1, // Smoothness of the line (optional)
    };
  });

  // Prepare chart data object for Chart.js
  const chartData = {
    labels: labels,
    datasets: datasets
  };

  console.log(chartData); // This will show the structure that will be passed to Chart.js
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
