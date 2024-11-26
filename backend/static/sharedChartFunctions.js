// sharedChartFunctions.js

export async function fetchGraphData(endpoint, callback) {
    try {
        const response = await fetch(endpoint);
        const data = await response.json();
        callback(data); // Pass the data to a callback function for further processing
    } catch (error) {
        console.error('Error fetching graph data:', error);
    }
}

export function prepareChartData(sensorData, metric, options = {}) {
    console.log(options.oneDay)
    const fullTimestamps = Object.keys(sensorData);
    const labels = fullTimestamps.map((timestamp, index) => {
        const date = new Date(timestamp);
        if(options.oneMonth){
            const month = String(date.getMonth() + 1).padStart(2, '0'); // months are zero-based
            const day = String(date.getDate()).padStart(2, '0');
            const formattedDate = `${day}.${month}.`;
            console.log(formattedDate); 
            return formattedDate;
            
        }
        
        const hour = date.getHours();
        const formattedHour = `${hour.toString().padStart(2, '0')}:00`;
        if (index === 0 || index === fullTimestamps.length - 1 || hour === 0 ) {
            // console.log('Yes')
            const formattedDate = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }); // e.g., "Nov 16"
            return `${formattedDate} ${formattedHour}`;
        }  
        
        return formattedHour;
    });
    
    const teams = new Set();

    Object.entries(sensorData).forEach(([timestamp, teamsData]) => {
        teamsData.forEach(team => {
            teams.add(team.team_id);
        });
    });

    const createMetricDataset = (metric) => {
        return Array.from(teams).map(teamId => {
            const color = getColorByTeamId(teamId);
            return {
                label: `Team ${capitalize(color)}`,
                data: fullTimestamps.map(timestamp => {
                    const teamData = sensorData[timestamp]?.find(team => team.team_id === teamId);
                    return teamData ? teamData[metric] : null;
                }),
                fill: false,
                borderColor: color,
                tension: 0.1
            };
        });
    };

    const datasets = createMetricDataset(metric);

    return {
        labels: labels,
        datasets: datasets
    };
}

export function getColorByTeamId(teamId) {
    const teamColors = {
        1: 'blue',
        2: 'black',
        3: 'green',
        4: 'pink',
        5: 'red',
        6: 'yellow'
    };
    return teamColors[teamId] || 'gray';
}

export function createChart(chartId, chartData, title, xAxisLabel) {
    const filteredDatasets = chartData.datasets.filter(dataset => {
        return !dataset.data.every(value => value === null || value === undefined);
    });

    if (filteredDatasets.length === 0) {
        console.log('No valid data to display for this metric.');
        return;
    }

    const ctx = document.getElementById(chartId).getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: filteredDatasets
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    type: 'category',
                    title: {
                        display: true,
                        text: xAxisLabel
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: title
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        title: function(tooltipItem) {
                            return 'Timestamp: ' + tooltipItem[0].label;
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

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}
