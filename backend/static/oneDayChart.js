// oneDayChart.js

import { fetchGraphData, prepareChartData, createChart } from './sharedChartFunctions.js';

fetchGraphData('/graph-data/one-day', (data) => {
    const tempData = prepareChartData(data, 'mean_temp', {oneDay : 'Yes'});
    const humiData = prepareChartData(data, 'mean_humi');
    const illuData = prepareChartData(data, 'mean_illu');

    createChart('tempChart', tempData, 'Temperature [°C]', 'Last 24 hours');
    createChart('humidityChart', humiData, 'Humidity [%]', 'Last 24 hours');
    createChart('illuminationChart', illuData, 'Illumination [lx]', 'Last 24 hours');
});
