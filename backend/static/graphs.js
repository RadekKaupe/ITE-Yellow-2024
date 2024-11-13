let graphDataArry = [];

async function fetchGraphData() {
    try {
        const response = await fetch('/graph-data');
        const data = await response.json();
        graphDataArry = data; // Save the fetched data
        console.log(graphDataArry);
        const preparedData = prepareChartData(graphDataArry); // Now data is available, call prepareChartData
        createCharts(preparedData); // Create the charts with the prepared data
    } catch (error) {
        console.error('Error fetching graph data:', error);
    }
}

// Function to format data for Chart.js
function prepareChartData(sensorData) {
    const teams = Object.keys(sensorData.sensor_data); // Access the 'sensor_data' field
    const labels = []; // We will collect all unique timestamps here
    const temperatureData = {}; // Will store temperature data for each team
    const humidityData = {}; // Will store humidity data for each team
    const illuminationData = {}; // Will store illumination data for each team

    // Iterate over each team
    teams.forEach(team => {
        const dataArray = sensorData.sensor_data[team]; // Get the array of data for this team

        // Prepare labels (timestamps) for the x-axis
        dataArray.forEach(data => {
            const timestamp = new Date(data.timestamp).toLocaleTimeString();
            if (!labels.includes(timestamp)) {
                labels.push(timestamp); // Add timestamp to the labels list (unique)
            }
        });

        // Initialize the arrays for each team
        temperatureData[team] = [];
        humidityData[team] = [];
        illuminationData[team] = [];

        // Prepare the actual sensor data for the chart
        dataArray.forEach(data => {
            temperatureData[team].push(data.temperature);
            humidityData[team].push(data.humidity);
            illuminationData[team].push(data.illumination);
        });
    });

    // Sort the labels to maintain the chronological order
    labels.sort();

    return {
        labels: labels,
        temperatureData: temperatureData,
        humidityData: humidityData,
        illuminationData: illuminationData
    };
}

// Function to create the charts with toggleable lines
function createCharts(data) {
    // Create the charts
    const tempChartCtx = document.getElementById('tempChart').getContext('2d');
    const humidityChartCtx = document.getElementById('humidityChart').getContext('2d');
    const illuminationChartCtx = document.getElementById('illuminationChart').getContext('2d');

    // Temperature Chart
    const tempChart = new Chart(tempChartCtx, {
        type: 'line',
        data: {
            labels: data.labels, // Use the sorted labels for the x-axis
            datasets: Object.keys(data.temperatureData).map(team => ({
                label: `Temperature - ${team}`,
                data: data.temperatureData[team],
                borderColor: getColorByTeamId(team),  // Use the color based on the team ID
                fill: false,
                hidden: false  // Initially, all datasets will be visible
            }))
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,  // Show the legend
                    position: 'top',
                    labels: {
                        boxWidth: 10,
                        padding: 20
                    }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });

    // Humidity Chart
    const humidityChart = new Chart(humidityChartCtx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: Object.keys(data.humidityData).map(team => ({
                label: `Humidity - ${team}`,
                data: data.humidityData[team],
                borderColor: getColorByTeamId(team),
                fill: false,
                hidden: false  // Initially, all datasets will be visible
            }))
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        boxWidth: 10,
                        padding: 20
                    }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });

    // Illumination Chart
    const illuminationChart = new Chart(illuminationChartCtx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: Object.keys(data.illuminationData).map(team => ({
                label: `Illumination - ${team}`,
                data: data.illuminationData[team],
                borderColor: getColorByTeamId(team),
                fill: false,
                hidden: false  // Initially, all datasets will be visible
            }))
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        boxWidth: 10,
                        padding: 20
                    }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}
// Function to generate random colors for different teams
function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
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
