document.addEventListener("DOMContentLoaded", () => {
    const ctx = document.getElementById('weatherChart').getContext('2d');
    if (!ctx || !window.weather) return;

    const canvas = document.getElementById('weatherChart');
    const styles = getComputedStyle(canvas);
    const data = {
        labels: window.weather.hourly.time,
        datasets: [{
            // label: 'System Temperature (°F)',
            data: window.weather.hourly.temp,
            borderColor: 'rgb(34, 139, 34)',
            // borderColor: styles.getPropertyValue('--line-color'),
            backgroundColor: 'rgba(34, 139, 34, 0.2)',
            // backgroundColor: styles.getPropertyValue('--fill-color'),
            fill: false,
            tension: 0.4
        },
        {
            // label: 'System Temperature (°F)',
            data: window.weather.hourly.cloud_cover,
            borderColor: 'rgb(34, 139, 34)',
            // borderColor: styles.getPropertyValue('--line-color'),
            backgroundColor: 'rgba(34, 139, 34, 0.2)',
            // backgroundColor: styles.getPropertyValue('--fill-color'),
            fill: false,
            tension: 0.4
        },
        {
            // label: 'System Temperature (°F)',
            data: window.weather.hourly.precipitation_probability,
            borderColor: 'rgb(34, 139, 34)',
            // borderColor: styles.getPropertyValue('--line-color'),
            backgroundColor: 'rgba(34, 139, 34, 0.2)',
            // backgroundColor: styles.getPropertyValue('--fill-color'),
            fill: false,
            tension: 0.4
        },
        {
            // label: 'System Temperature (°F)',
            data: window.weather.hourly.precipitation,
            borderColor: 'rgb(34, 139, 34)',
            // borderColor: styles.getPropertyValue('--line-color'),
            // backgroundColor: 'rgba(34, 139, 34, 0.2)',
            // backgroundColor: styles.getPropertyValue('--fill-color'),
            fill: false,
            tension: 0.4
        },
        ]
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
                y: {
                    grid:{
                        color: 'rgba(225, 226, 224, .75)'
                    },
                    ticks: {
                        color: '#E1E2E0'
                    },
                    title: {
                        display: true,
                        text: 'Temperature',
                        color: '#E1E2E0'
                    }
                }
            }
        }
    };

    const tempChart = new Chart(ctx, config);
});