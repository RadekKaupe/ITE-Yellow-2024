// oneMonthChart.js
console.log("Start");
import { fetchGraphData, prepareChartData, createChart } from './sharedChartFunctions.js';

prepareChartData

fetchGraphData('/graph-data/one-month', (data) => {
    const tempData = prepareChartData(data, 'mean_temp', {oneMonth : 'yes'});
    const humiData = prepareChartData(data, 'mean_humi', {oneMonth : 'yes'});
    const illuData = prepareChartData(data, 'mean_illu', {oneMonth : 'yes'});

    createChart('tempChart', tempData, 'Temperature [°C]', 'Last 30 days');
    createChart('humidityChart', humiData, 'Humidity [%]', 'Last 30 days');
    createChart('illuminationChart', illuData, 'Illumination [lx]', 'Last 30 days');
});
