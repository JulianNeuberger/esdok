import React from "react";

import {Entity} from "../../services/metaModelService";
import {Button, Form, Select} from "antd";
import {CloseOutlined, DownOutlined} from "@ant-design/icons";
import {Handle, Position} from "@xyflow/react";
import TextArea from "antd/es/input/TextArea";

interface Props  {
    data: {
        entity: Entity;
    };
}

const MetaModelNode = ({ data }: Props) => {
    const [isOpen, setIsOpen] = React.useState(false);
    const [entity, setEntity] = React.useState(data.entity);

    const renderContent = () => {
        if(!isOpen) return <>{entity.name}</>;
        return (
            <Form>
                <Form.Item>{entity.name}</Form.Item>
                <Form.Item>
                    <TextArea
                        value={entity.description}
                        placeholder={"description"}
                        onChange={e => {
                            setEntity({
                                ...entity,
                                description: e.target.value
                            })
                        }}
                    />
                </Form.Item>
            </Form>
        );
    }

    return (
        <div style={{
            borderRadius: 5,
            border: "solid 1px black",
            padding: 10,
            paddingRight: 50,
            backgroundColor: "white"
        }}>
            <Button
                icon={isOpen ? <CloseOutlined /> : <DownOutlined />}
                shape={"circle"}
                type={"text"}
                size={"small"}
                onClick={() => setIsOpen(!isOpen)}
                style={{
                    position: "absolute",
                    top: 10,
                    right: 5,
                }}
            />
            <Handle type={"source"} position={Position.Top} />
            {renderContent()}
            <Handle type={"target"} position={Position.Bottom} />
        </div>
    );
}

export default MetaModelNode;