import React from 'react';
import { S3EmptyState } from '@smart3ai/design-system';

const CrudEmptyState = ({ message, colSpan }) => {
  return <S3EmptyState message={message} colSpan={colSpan} />;
};

export default CrudEmptyState;
