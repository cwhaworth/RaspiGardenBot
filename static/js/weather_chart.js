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
            borderColor: 'rgb(34, 139, 34)',
            // borderColor: styles.getPropertyValue('--line-color'),
            backgroundColor: 'rgba(34, 139, 34, 0.2)',
            // backgroundColor: styles.getPropertyValue('--fill-color'),
            fill: false,
            yAxisID: 'yTemp',
            tension: 0.4
        },
        {
            label: 'Precipitation (In.)',
            data: window.weather.hourly.precipitation,
            borderColor: 'rgb(34, 139, 34)',
            // borderColor: styles.getPropertyValue('--line-color'),
            // backgroundColor: 'rgba(34, 139, 34, 0.2)',
            // backgroundColor: styles.getPropertyValue('--fill-color'),
            fill: false,
            yAxisID: 'yPrecip',
            tension: 0.4
        },
        {
            label: 'Cloud Cover',
            data: window.weather.hourly.cloud_cover,
            borderColor: 'rgb(34, 139, 34)',
            // borderColor: styles.getPropertyValue('--line-color'),
            backgroundColor: 'rgba(34, 139, 34, 0.2)',
            // backgroundColor: styles.getPropertyValue('--fill-color'),
            fill: false,
            yAxisID: 'yPercent',
            tension: 0.4
        },
        {
            label: 'Precipitation %',
            data: window.weather.hourly.precipitation_probability,
            borderColor: 'rgb(34, 139, 34)',
            // borderColor: styles.getPropertyValue('--line-color'),
            backgroundColor: 'rgba(34, 139, 34, 0.2)',
            // backgroundColor: styles.getPropertyValue('--fill-color'),
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
                    display: false,
                    position: 'top'
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
                        color: '#E1E2E0'
                    },
                    title: {
                        display: true,
                        text: 'Inch',
                        color: '#E1E2E0'
                    }
                },
                yPrecip: {
                    type: 'linear',
                    position: 'left',
                    grid:{
                        drawOnChartArea: false
                    },
                    ticks: {
                        color: '#E1E2E0'
                    },
                    title: {
                        display: true,
                        text: 'Precipitation (In)',
                        color: '#E1E2E0'
                    }
                },
                yPercent: {
                    type: 'linear',
                    position: 'left',
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