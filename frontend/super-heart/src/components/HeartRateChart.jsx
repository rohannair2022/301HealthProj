import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './Charts.css';

const HeartRateChart = ({ data }) => {
  return (
    <div className="chart-container">
      <h3>7-Day Heart Rate Progress</h3>
      
      {/* Accessible table for screen readers only */}
      <table className="visually-hidden" aria-label="Heart rate data for the past 7 days">
        <caption>Heart rate measurements (beats per minute)</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Heart Rate (BPM)</th>
          </tr>
        </thead>
        <tbody>
          {data && data.map((item, index) => (
            <tr key={index}>
              <th scope="row">{item.date}</th>
              <td>{item.heart_rate} beats per minute</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row">Average</th>
            <td>
              {data && data.length > 0 
                ? Math.round(data.reduce((sum, day) => sum + (day.heart_rate || 0), 0) / data.length)
                : 'No data'} beats per minute
            </td>
          </tr>
        </tfoot>
      </table>
      
      {/* Visual chart hidden from screen readers */}
      <div className="chart-wrapper" aria-hidden="true">
        <ResponsiveContainer width="99%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis
              dataKey="date.date"
              stroke="var(--text-secondary)"
              tick={{ fill: 'var(--text-secondary)', angle: -90, textAnchor: 'end' }} 
              interval={0}
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
                `Date: ${props.payload.date}`, 
              ]}
            />
            <Line
              type="monotone"
              dataKey="heart_rate"
              stroke="#ff6b6b"
              strokeWidth={2}
              dot={{ fill: '#ff6b6b', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default HeartRateChart;