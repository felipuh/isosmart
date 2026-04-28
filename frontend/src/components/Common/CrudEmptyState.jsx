import React from 'react';
const CrudEmptyState = ({ message, colSpan }) => {
  if (colSpan) {
    return (
      <tr>
        <td colSpan={colSpan} className="px-6 py-8 text-center text-gray-400">
          {message}
        </td>
      </tr>
    );
  }

  return <div className="py-8 text-center text-gray-400">{message}</div>;
};

export default CrudEmptyState;
