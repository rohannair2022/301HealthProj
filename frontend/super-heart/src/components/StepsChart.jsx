import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './Charts.css';

const StepsChart = ({ data }) => {
  return (
    <div className="chart-container">
      <h3>7-Day Step Progress</h3>
      
      {/* Accessible table for screen readers only */}
      <table className="visually-hidden" aria-label="Step count data for the past 7 days">
        <caption>Daily step measurements</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Steps</th>
          </tr>
        </thead>
        <tbody>
          {data && data.map((item, index) => (
            <tr key={index}>
              <th scope="row">{item.date}</th>
              <td>{item.steps} steps</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row">Total</th>
            <td>
              {data && data.length > 0 
                ? data.reduce((sum, day) => sum + (day.steps || 0), 0)
                : 'No data'} steps
            </td>
          </tr>
          <tr>
            <th scope="row">Average per day</th>
            <td>
              {data && data.length > 0 
                ? Math.round(data.reduce((sum, day) => sum + (day.steps || 0), 0) / data.length)
                : 'No data'} steps
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