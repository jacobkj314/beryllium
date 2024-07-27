import React, {useState} from 'react';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadProps, FormProps } from 'antd';
import { Button, message, Upload, Typography, Form, Space, Alert } from 'antd';

export default function UploadImage() {

  const { Title } = Typography;

  const [disableButton, setDisableButton] = useState<boolean>(true);

  const onFinish: FormProps['onFinish'] = (values) => {
    console.log('Success:', values);
  };
  
  const onFinishFailed: FormProps['onFinishFailed'] = (errorInfo) => {
    console.log('Failed:', errorInfo);
  };

  const props: UploadProps = {
    name: 'file',
    action: 'https://660d2bd96ddfa2943b33731c.mockapi.io/api/upload',
    headers: {
      authorization: 'authorization-text',
    },
    onChange(info) {
      if (info.file.status !== 'uploading') {
        console.log(info.file, info.fileList);
      }
      if (info.file.status === 'done') {
        message.success(`${info.file.name} file uploaded successfully`);
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} file upload failed.`);
      }
    },
  };

  return (
    <div style={{ textAlign:'center', marginTop:'50px'}}>
        <Title style={{display:'block'}}>BERYLLIUM</Title>

        <Form
          name="basic"
          labelCol={{ span: 8 }}
          wrapperCol={{ span: 16 }}
          style={{ display:'inline-block', maxWidth: 600 }}
          initialValues={{ remember: true }}
          onFinish={onFinish}
          onFinishFailed={onFinishFailed}
          autoComplete="off"
        >
        <Form.Item label="Face Image: ">
          <Upload {...props}>
            <Button icon={<UploadOutlined />}>Click to Upload</Button>
          </Upload>
        </Form.Item>

        <Form.Item label="Away Image: ">
          <Upload {...props}>
            <Button icon={<UploadOutlined />}>Click to Upload</Button>
          </Upload>
        </Form.Item>

        <Form.Item wrapperCol={{ offset: 2, span:20 }}>
          <Alert
            message="Info Text"
            description={<p> By uploading, you agree that the owners/admins of this Beryllium instance may retain a copy of your images until tomorrow, when the server resets. Your images are never saved to permanent storage (such as a hard drive). If you would like to keep a copy of your images, be sure to save it locally or access Beryllium using an application designed to archive your images. For more details, visit <a href="https://github.com/jacobkj314/beryllium">https://github.com/jacobkj314/beryllium</a>.</p>}
            type="info"
            action={
              <Space direction="vertical">
                <Button size="small" type="primary" onClick={() => setDisableButton(false)}>
                  Accept
                </Button>
                <Button size="small" danger ghost onClick={() => setDisableButton(true)}>
                  Decline
                </Button>
              </Space>
            }
          />
        </Form.Item>

        <Form.Item wrapperCol={{ offset: 8, span:8 }}>
          <Button type="primary" htmlType="submit" disabled={disableButton}>
            Upload Images
          </Button>
        </Form.Item>
        </Form>   
    </div>
)}