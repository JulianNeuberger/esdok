import React from "react";

import {Aspect, Entity, MetaModelService} from "../../services/metaModelService";
import {Button, Select, Space} from "antd";
import {CloseOutlined, DownOutlined} from "@ant-design/icons";
import {Handle, Position} from "@xyflow/react";
import TextArea from "antd/es/input/TextArea";

import "./MetaModelNode.css";

interface Props  {
    data: {
        entity: Entity;
        aspects: Aspect[];
        metaModel: string;
    };
}

const metaModelService = new MetaModelService();

const MetaModelNode = ({ data }: Props) => {
    const [isOpen, setIsOpen] = React.useState(false);
    const [entity, setEntity] = React.useState(data.entity);

    const renderContent = () => {
        if(!isOpen) return;
        return (
            <Space direction={"vertical"} style={{marginTop: 10, pointerEvents: "all"}}>
                <Select
                    className={"aspect"}
                    onChange={(aspectName, e) => {
                        const newAspect = data.aspects.find(a => a.name == aspectName);
                        if(!newAspect) {
                            console.error(`Could not find ${aspectName} in aspects!`)
                            return;
                        }
                        console.log(`${aspectName}`, newAspect)
                        setEntity({...entity, aspect: newAspect})
                    }}
                    value={entity.aspect.name}
                >
                    {
                        data.aspects?.map(a => {
                            return (<Select.Option value={a.name} aspect={a} key={a.name}>{a.name}</Select.Option>);
                        })
                    }
                </Select>
                <TextArea
                    className={"description"}
                    value={entity.description}
                    placeholder={"description"}
                    onChange={e => {
                        setEntity({
                            ...entity,
                            description: e.target.value
                        })
                    }}
                />
                <Button
                    className={"save"}
                    type={"primary"}
                    onClick={async () => {
                        if(!data?.metaModel) return;
                        await metaModelService.patchModel(data.metaModel, [entity], [])
                    }}
                >
                    Save
                </Button>
            </Space>
        );
    }

    return (
        <div className={`meta-node ${isOpen ? "open" : ""}`}>
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
            <div className={"name"}>{entity.name}</div>
            {renderContent()}
            <Handle type={"target"} position={Position.Bottom} />
        </div>
    );
}

export default MetaModelNode;