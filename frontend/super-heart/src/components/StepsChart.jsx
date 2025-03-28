import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './Charts.css';

const StepsChart = ({ data }) => {
  return (
    <div className="chart-container">
      <h3>7-Day Step Progress</h3>
      <div className="chart-wrapper" aria-label="Line chart showing the 7-day step progress. The x-axis represents the date, and the y-axis represents the number of steps.">
        <ResponsiveContainer width="99%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis
              dataKey="date.date"
              stroke="var(--text-secondary)"
              tick={{ fill: 'var(--text-secondary)', angle: -90, textAnchor: 'end' }} // Rotate labels vertically
              interval={0} // Ensure all dates are shown
            />
            <YAxis
              stroke="var(--text-secondary)"
              tick={{ fill: 'var(--text-secondary)' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
              }}
              formatter={(value, name, props) => [
                value,
                `Date: ${props.payload.date}`, // Display the date in the tooltip
              ]}
            />
            <Line
              type="monotone"
              dataKey="steps"
              stroke="var(--highlight-color)"
              strokeWidth={2}
              dot={{ fill: 'var(--highlight-color)', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default StepsChart;