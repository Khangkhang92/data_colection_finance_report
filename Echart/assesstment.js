let data = context.panel.data;

// Extract categories and series data in a single pass
const categories = [];
const seriesData = data.series
  .filter(s => s.refId === "A")
  .flatMap(s => {
    if (categories.length === 0) {
      categories.push(...s.fields.find(f => f.name === "Time").values);
    }
    return s.fields
      .filter(field => !["year", "quarter", "Time"].includes(field.name))
      .map(field => ({
        data: field.values,
        type: 'bar',
        name: field.name,
        stack: 'total',
      }));
  });

// Calculate dynamic legend settings
const numberOfSeries = seriesData.length;
const legendItemGap = numberOfSeries > 10 ? 5 : 15;
const legendBottomMargin = numberOfSeries > 10 ? '10%' : '0%';

// Helper function for number formatting
const formatNumber = value => value.toLocaleString();

// Return optimized configuration
return {
  grid: {
    bottom: "20%",
    containLabel: true,
    left: "3%",
    right: "4%",
    top: "4%"
  },
  series: seriesData,
  xAxis: {
    data: categories,
    type: "category",
    axisLabel: {
      interval: 0,
      rotate: 45
    }
  },
  yAxis: {
    type: "value",
    axisLabel: {
      formatter: formatNumber
    }
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    },
    formatter: params => {
      return `<div>${params[0].name}</div>` +
        params.map(item => 
          `<div style="color:${item.color}"><strong>${item.seriesName}:</strong> ${formatNumber(item.value)}</div>`
        ).join('');
    }
  },
  legend: {
    bottom: '0%',
    left: 'center',
    padding: [10, 0],
    itemGap: legendItemGap,
    textStyle: {
      fontSize: 12
    }
  },
  dataZoom: [{
    type: 'slider',
    xAxisIndex: 0,
    filterMode: 'filter',
    height: 20,
    bottom: 0,
    start: 0,
    end: 100,
    handleIcon: 'path://M306.1,413c0,2.2-1.8,4-4,4h-59.8c-2.2,0-4-1.8-4-4V200.8c0-2.2,1.8-4,4-4h59.8c2.2,0,4,1.8,4,4V413z',
    handleSize: '110%'
  }]
};
