let graphDataArry = [];

async function fetchGraphData() {
    try {
        const response = await fetch('/graph-data');
        let data = await response.json();
        // data = {
        //     "2024-11-09T10:00:00": [
        //         { "team_id": 1, "mean_temp": 22.5, "mean_humi": 60, "mean_illu": 300 }
        //     ],
        //     "2024-11-10T10:00:00": [
        //         { "team_id": 1, "mean_temp": 22.5, "mean_humi": 60, "mean_illu": 300 }
        //     ],
        //     "2024-11-10T19:00:00": [
        //         { "team_id": 1, "mean_temp": 22.245, "mean_humi": 54.22, "mean_illu": 284.08 },
        //         { "team_id": 2, "mean_temp": 23.74, "mean_humi": 50.46, "mean_illu": 482.632 }
        //     ]
        // };
        graphDataArry = data; // Save the fetched data
        console.log(graphDataArry);
        const temp_data = prepareChartData(graphDataArry, 'mean_temp'); 
        const humi_data = prepareChartData(graphDataArry, 'mean_humi'); 
        const illu_data = prepareChartData(graphDataArry, 'mean_illu'); 


        console.log(temp_data)
        console.log(humi_data)
        console.log(illu_data)


        createChart('tempChart', temp_data, 'Temperature');
        createChart('humidityChart', humi_data, 'Humidity');
        createChart('illuminationChart', illu_data, 'Illumination');
    } catch (error) {
        console.error('Error fetching graph data:', error);
    }
}
function prepareChartData(sensorData, metric) {
    const labels = Object.keys(sensorData); // Timestamps as labels
    const teams = new Set(); // To store unique team_ids

    // Loop through the data to gather unique teams
    Object.entries(sensorData).forEach(([timestamp, teamsData]) => {
      teamsData.forEach(team => {
        teams.add(team.team_id); // Add team_id to the set (only unique ids will be kept)
      });
    });

    // Create datasets for the specific metric (temperature, humidity, or illumination)
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

    // Create datasets for the metric
    const datasets = createMetricDataset(metric, metric.charAt(0).toUpperCase() + metric.slice(1));
    
    // Return chartData in a format suitable for Chart.js
    const chartData = {
      labels: labels, // Timestamps as x-axis labels
      datasets: datasets
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

function createChart(chartId, chartData, title) {

      const filteredDatasets = chartData.datasets.filter(dataset => {
        return !dataset.data.every(value => value === null || value === undefined);
      });

// If no valid datasets remain, do not create the chart
    if (filteredDatasets.length === 0) {
        console.log('No valid data to display for this metric.');
        return;
    }
    console.log("Filtered Datasets:", filteredDatasets);   
    const ctx = document.getElementById(chartId).getContext('2d');
      
    new Chart(ctx, {
      type: 'line', // Change this to 'bar', 'radar', etc. if needed
      data: {
        labels: chartData.labels, // Use the same labels
        datasets: filteredDatasets // Use filtered datasets
    },
      options: {
        responsive: true,
        scales: {
          x: {
            type: 'category', // Use 'category' for timestamps on the x-axis
            title: {
              display: true,
              text: 'Timestamp' // Label for the x-axis
            }
          },
          y: {
            title: {
              display: true,
              text: title // Title of the y-axis based on the metric
            }
          }
        },
        plugins: {
          legend: {
            position: 'top', // Legend position
          },
          tooltip: {
            callbacks: {
              // Customize tooltips
              title: function(tooltipItem) {
                return 'Timestamp: ' + tooltipItem[0].label; // Show timestamp in tooltip title
              },
              label: function(tooltipItem) {
                const team = tooltipItem.dataset.label;
                const value = tooltipItem.raw;
                return `${team}: ${value}`;
              }
            }
          }
        }
      }
    });
  }

  // Start fetching and plotting data
fetchGraphData();
