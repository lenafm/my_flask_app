document.addEventListener('DOMContentLoaded', function() {
    const mapDiv = document.getElementById('choropleth-map');
    const layout = {
        geo: {
            scope: 'europe',
            showframe: true,
            showcoastlines: false,
            projection: {
                type: 'mercator'
            }
        },
        title: 'UK Parliamentary Constituencies'
    };

    const initialData = [{
        type: 'choropleth',
        locationmode: 'country names',
        locations: ['England', 'Scotland', 'Wales'],  // These should match exactly with the location names used in your GeoJSON
        z: [1, 2, 3],  // Example data values for each location
        text: ['England', 'Scotland', 'Wales'],  // Optional: Text displayed when hovering over locations
        autocolorscale: true
    }];    

    Plotly.newPlot('choropleth-map', initialData, layout);

    // Functions and event listeners
    function updateMap(dataType) {
        const url = `/choropleth/data?type=${dataType}`;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                Plotly.react(mapDiv, data, layout);
            })
            .catch(error => console.error('Error fetching data:', error));
    }
});
