document.addEventListener("DOMContentLoaded", () => {
    // const yCtx = document.getElementById('yAxisChart').getContext('2d');
    const ctx = document.getElementById('weatherChart').getContext('2d');
    const yLegend = document.getElementById('yAxisLegend');
    // if (!ctx || ! yCtx || !yLegend || !window.weather) return;
    if (!ctx | !yLegend) return;

    const canvas = document.getElementById('weatherChart');
    const styles = getComputedStyle(canvas);

    const dataset = [{
            label: 'Temperature (°F)',
            data: window.weather.hourly.temp,
            borderColor: styles.getPropertyValue('--temperature-color'),
            backgroundColor: styles.getPropertyValue('--temperature-color'),
            fill: true,
            yAxisID: 'yTemp',
            tension: 0.4
        },
        // {
        //     label: 'Precipitation (In.)',
        //     data: window.weather.hourly.precipitation,
        //     borderColor: styles.getPropertyValue('--precipitation-color'),
        //     backgroundColor: styles.getPropertyValue('--precipitation-color'),
        //     fill: true,
        //     yAxisID: 'yPrecip',
        //     tension: 0.4
        // },
        {
            label: 'Cloud Cover',
            data: window.weather.hourly.cloud_cover,
            borderColor: styles.getPropertyValue('--cloud-cover-color'),
            backgroundColor: styles.getPropertyValue('--cloud-cover-color'),
            fill: true,
            yAxisID: 'yPercent',
            tension: 0.4
        },
        {
            label: 'Precipitation %',
            data: window.weather.hourly.precipitation_probability,
            borderColor: styles.getPropertyValue('--precipitation-percent-color'),
            backgroundColor: styles.getPropertyValue('--precipitation-percent-color'),
            fill: true,
            yAxisID: 'yPercent',
            tension: 0.4,
        }]

    const legendItems = [
            {
                label: dataset[0].label, 
                color: styles.getPropertyValue('--temperature-color')
            },
            {
                label: dataset[1].label, 
                color: styles.getPropertyValue('--precipitation-color')
            },
            {    
                label: dataset[2].label, 
                color: styles.getPropertyValue('--cloud-cover-color')
            },
            {
                label: dataset[3].label, 
                color: styles.getPropertyValue('--precipitation-percent-color')
            }
    ];
    const data = {
        labels: window.weather.hourly.time,
        datasets: dataset
    };

    const config = {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                    position: 'bottom',
                    align: 'start',
                    labels: {
                        color: '#E1E2E0'
                    }
                },
                title: {
                    display: false,
                    text: 'System Temperature Over Time'
                }
            },
            scales: {
                x: {
                    grid:{
                        color: 'rgba(225, 226, 224, .75)'
                    },
                    ticks: {
                        color: '#E1E2E0',
                        autoSkip: false
                    },
                    title: {
                        display: false,
                        text: 'Timestamp',
                        color: '#E1E2E0'
                    }
                },
                yPercent: {
                    type: 'linear',
                    position: 'left',
                    min: 0,
                    max: 100,
                    grid:{
                        drawOnChartArea: false
                    },
                    ticks: {
                        color: '#E1E2E0'
                    },
                    title: {
                        display: true,
                        text: '% Chance',
                        color: '#E1E2E0'
                    }
                },
                // yPrecip: {
                //         type: 'linear',
                //         position: 'left',
                //         min: 0,
                //         max: 20,
                //         grid:{
                //             drawOnChartArea: false
                //         },
                //         ticks: {
                //             color: styles.getPropertyValue('--precipitation-color')
                //         },
                //         title: {
                //             display: true,
                //             text: 'Precipitation (In)',
                //             color: styles.getPropertyValue('--precipitation-color')
                //         }
                //     },
                yTemp: {
                    type: 'linear',
                    position: 'left',
                    min: 0,
                    max: 120,
                    grid:{
                        drawOnChartArea: false,
                        color: 'rgba(225, 226, 224, .75)'
                    },
                    ticks: {
                        color: styles.getPropertyValue('--temperature-color')
                    },
                    title: {
                        display: true,
                        text: 'Temperature (°F)',
                        color: styles.getPropertyValue('--temperature-color')
                    }
                }
                
            }
        }
    };

    yLegend.innerHTML = legendItems.map(item => `
    <div class="col">
        <span style="width:12px;height:12px;background:${item.color};display:inline-block;margin-right:6px;"></span>
        <span style="color:#E1E2E0;font-size:12px;">${item.label}</span>
    </div>
    `).join('');

    const tempChart = new Chart(ctx, config);
});