let data = context.panel.data;

// Initialize arrays for series data
let seriesData = [];
let categories = [];

// Extract data from series
const { categories: extractedCategories, seriesData: extractedSeriesData } = data.series.reduce((acc, s) => {
  if (s.refId === "A") {
    if (acc.categories.length === 0) {
      acc.categories = s.fields.find((f) => f.name === "Time").values;
    }

    s.fields.forEach((field) => {
      if (!["year", "quarter", "Time"].includes(field.name)) {
        const seriesConfig = getSeriesConfig(field.name);
        acc.seriesData.push({
          data: field.values,
          name: field.name,
          ...seriesConfig
        });
      }
    });
  }
  return acc;
}, { categories: [], seriesData: [] });

// Calculate dynamic legend settings
const numberOfSeries = extractedSeriesData.length;
const legendConfig = {
  itemGap: numberOfSeries > 10 ? 5 : 15,
  bottom: numberOfSeries > 10 ? '10%' : '0%',
  selected: extractedSeriesData.reduce((acc, series) => {
    acc[series.name] = series.show !== false;
    return acc;
  }, {})
};

// Return configuration with dynamic series, stacked bars, and adjusted legend
return {
  grid: {
    bottom: "20%", // Increased to accommodate the dataZoom
    containLabel: true,
    left: "3%",
    right: "4%",
    top: "4%"
  },
  series: extractedSeriesData,
  xAxis: {
    data: extractedCategories,
    type: "category"
  },
  yAxis: {
    type: "value",
    axisLabel: {
      formatter: value => value.toLocaleString()
    }
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    formatter: params => formatTooltip(params)
  },
  legend: {
    bottom: '10%', // Adjusted to make room for dataZoom
    left: 'center',
    padding: [10, 0],
    textStyle: { fontSize: 12 },
    ...legendConfig
  },
  dataZoom: [
    {
      type: 'slider',
      xAxisIndex: 0,
      start: 0,
      end: 100,
      bottom: '20%'
    }
  ]
};

// Helper functions
function getSeriesConfig(fieldName) {
  const config = {
    type: 'bar',
    lineStyle: {},
    color: undefined,
    show: true // Default to showing the series
  };

  switch (fieldName) {
    case 'Dòng tiền từ đầu tư':
      config.color = 'orange';
      break;
    case 'Dòng tiền từ kinh doanh':
      config.color = 'green';
      break;
    case 'Dòng tiền từ tài chính':
      config.color = 'red';
      break;
    case 'Dòng tiền thuần trong kỳ':
      config.type = 'line';
      config.lineStyle = { smooth: true };
      break;
    case 'Tiền đầu kỳ':
    case 'Tiền cuối kỳ':
    case 'Ảnh hưởng bởi tỷ giá':
      config.show = false; // Initially hide these series
      break;
  }

  return config;
}

function formatTooltip(params) {
  return `<div>${params[0].name}</div>` +
    params.map(item =>
      `<div style="color:${item.color}"><strong>${item.seriesName}:</strong> ${item.value.toLocaleString()}</div>`
    ).join('');
}
