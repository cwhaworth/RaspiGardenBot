document.addEventListener("DOMContentLoaded", () => {
    const ctx = document.getElementById('weatherChart').getContext('2d');
    if (!ctx || !window.weather) return;

    const canvas = document.getElementById('weatherChart');
    const styles = getComputedStyle(canvas);
    const data = {
        labels: window.weather.hourly.time,
        datasets: [{
            label: 'Temperature (°F)',
            data: window.weather.hourly.temp,
            // borderColor: 'rgb(34, 139, 34)',
            borderColor: styles.getPropertyValue('--temperature-color'),
            // backgroundColor: 'rgba(34, 139, 34, 0.2)',
            backgroundColor: styles.getPropertyValue('--temperature-color'),
            fill: false,
            yAxisID: 'yTemp',
            tension: 0.4
        },
        {
            label: 'Precipitation (In.)',
            data: window.weather.hourly.precipitation,
            // borderColor: 'rgba(9, 149, 214, 0.2)',
            borderColor: styles.getPropertyValue('--precipitation-color'),
            // backgroundColor: 'rgba(9, 149, 214, 0.2)',
            backgroundColor: styles.getPropertyValue('--precipitation-color'),
            fill: false,
            yAxisID: 'yPrecip',
            tension: 0.4
        },
        {
            label: 'Cloud Cover',
            data: window.weather.hourly.cloud_cover,
            // borderColor: 'rgba(170, 173, 170, 1)',
            borderColor: styles.getPropertyValue('--cloud-cover-color'),
            // backgroundColor: 'rgba(170, 173, 170, 1)',
            backgroundColor: styles.getPropertyValue('--cloud-cover-color'),
            fill: false,
            yAxisID: 'yPercent',
            tension: 0.4
        },
        {
            label: 'Precipitation %',
            data: window.weather.hourly.precipitation_probability,
            // borderColor: 'rgba(9, 149, 214, 0.2)',
            borderColor: styles.getPropertyValue('--precipitation-color'),
            // backgroundColor: 'rgba(9, 149, 214, 0.2)',
            backgroundColor: styles.getPropertyValue('--precipitation-color'),
            fill: false,
            yAxisID: 'yPercent',
            tension: 0.4
        }]
    };

    const config = {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom left'
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
                        color: '#E1E2E0'
                    },
                    title: {
                        display: true,
                        text: 'Timestamp',
                        color: '#E1E2E0'
                    }
                },
                yTemp: {
                    type: 'linear',
                    position: 'left',
                    grid:{
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
                },
                yPrecip: {
                    type: 'linear',
                    position: 'left',
                    min: 0,
                    grid:{
                        drawOnChartArea: false
                    },
                    ticks: {
                        color: styles.getPropertyValue('--precipitation-color')
                    },
                    title: {
                        display: true,
                        text: 'Precipitation (In)',
                        color: styles.getPropertyValue('--precipitation-color')
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
                }
            }
        }
    };

    const tempChart = new Chart(ctx, config);
});