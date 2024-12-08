// oneMonthChart.js
console.log("Start");
import { fetchGraphData, prepareChartData, createChart } from './sharedChartFunctions.js';

prepareChartData

fetchGraphData('/graph-data/one-week', (data) => {
    const tempData = prepareChartData(data, 'mean_temp', {oneWeek : 'yes'});
    const humiData = prepareChartData(data, 'mean_humi', {oneWeek : 'yes'});
    const illuData = prepareChartData(data, 'mean_illu', {oneWeek : 'yes'});

    createChart('tempChart', tempData, 'Temperature [°C]', 'Last 7 days');
    createChart('humidityChart', humiData, 'Humidity [%]', 'Last 7 days');
    createChart('illuminationChart', illuData, 'Illumination [lx]', 'Last 7 days');
});
